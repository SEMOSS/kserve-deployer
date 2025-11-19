import logging
import time
from typing import Dict, List, Optional
from kubernetes import client, config
from kubernetes.client import ApiException
from kubernetes.watch import Watch
from pydantic import BaseModel
from src.config.config import config as app_config
from src.aws.aws_manager import AWSManager


class HTTPRouteInfo(BaseModel):
    name: str
    namespace: Optional[str] = None
    paths: List[str]


class KubeManager:
    def __init__(self, in_cluster: bool = False):
        self.logger = logging.getLogger(__name__)
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()

        self.core = client.CoreV1Api()
        self.custom = client.CustomObjectsApi()
        self.aws = AWSManager()
        self.namespace = app_config.MODEL_NAMESPACE
        self.KServe_GROUP = app_config.KSERVE_GROUP
        self.KServe_VERSION = app_config.KSERVE_VERSION
        self.KServe_PLURAL = app_config.KSERVE_PLURAL
        self.hostname = app_config.HOSTNAME

    def _ensure_inferenceservice(self, obj: dict) -> dict:
        meta = obj.setdefault("metadata", {})
        name = meta.get("name")

        try:
            self.logger.info(f"Creating InferenceService {name} in ns {self.namespace}")
            created = self.custom.create_namespaced_custom_object(
                group=self.KServe_GROUP,
                version=self.KServe_VERSION,
                namespace=self.namespace,
                plural=self.KServe_PLURAL,
                body=obj,
            )
            return created
        except ApiException as e:
            if e.status != 409:
                # 409 = AlreadyExists; otherwise bubble up
                raise
            self.logger.info(
                f"Exists; patching InferenceService {name} in ns {self.namespace}"
            )
            patched = self.custom.patch_namespaced_custom_object(
                group=self.KServe_GROUP,
                version=self.KServe_VERSION,
                namespace=self.namespace,
                plural=self.KServe_PLURAL,
                name=name,
                body=obj,
            )
            return patched

    def _wait_ready(
        self,
        name: str,
        timeout_sec: int = 600,
        poll_sec: int = 5,
    ) -> bool:
        """Wait until status.conditions has Ready=True."""
        self.logger.info(
            f"Waiting for InferenceService/{name} to be Ready (timeout {timeout_sec}s)"
        )
        w = Watch()
        start = time.time()
        while True:
            if time.time() - start > timeout_sec:
                self.logger.warning("Timed out waiting for Ready")
                return False
            try:
                obj = self.custom.get_namespaced_custom_object(
                    group=self.KServe_GROUP,
                    version=self.KServe_VERSION,
                    namespace=self.namespace,
                    plural=self.KServe_PLURAL,
                    name=name,
                )
            except ApiException as e:
                if e.status == 404:
                    time.sleep(poll_sec)
                    continue
                raise

            status = (obj or {}).get("status", {})
            conditions = status.get("conditions", []) or []
            for c in conditions:
                if c.get("type") == "Ready":
                    if c.get("status") == "True":
                        self.logger.info("InferenceService is Ready")
                        return True
                    if c.get("status") == "False":
                        break
            time.sleep(poll_sec)

    def _wait_deleted(
        self,
        name: str,
        namespace: str,
        timeout_sec: int = 300,
        poll_sec: int = 5,
    ) -> bool:
        """
        Wait until the InferenceService no longer exists (GET returns 404).
        This is roughly equivalent to waiting for `kubectl delete` to complete.
        """
        self.logger.info(
            f"Waiting for InferenceService/{name} in ns {namespace} to be deleted "
            f"(timeout {timeout_sec}s)"
        )
        start = time.time()
        while True:
            if time.time() - start > timeout_sec:
                self.logger.warning("Timed out waiting for deletion")
                return False

            try:
                self.custom.get_namespaced_custom_object(
                    group=self.KServe_GROUP,
                    version=self.KServe_VERSION,
                    namespace=namespace,
                    plural=self.KServe_PLURAL,
                    name=name,
                )

                time.sleep(poll_sec)
            except ApiException as e:
                if e.status == 404:
                    self.logger.info(
                        f"InferenceService/{name} in ns {namespace} has been deleted"
                    )
                    return True

                self.logger.exception(
                    f"Error while waiting for deletion of {name}: {e}"
                )
                return False

    async def deploy_inference_service(
        self, model_name: str, semoss_id: str, wait: bool = True
    ):
        self.logger.info(
            f"Deploying inference service for model={model_name}, semoss_id={semoss_id}"
        )

        obj = self.aws.read_deployment_yaml(f"{model_name}.yaml")
        if not obj:
            self.logger.error(f"Deployment YAML for model {model_name} not found.")
            return False

        if not isinstance(obj, dict):
            self.logger.error(
                f"Expected dict from AWSManager, got {type(obj).__name__}"
            )
            return False

        if obj.get("kind") != "InferenceService":
            self.logger.error("Provided YAML is not an InferenceService.")
            return False

        meta = obj.setdefault("metadata", {})
        name = meta.get("name", None)
        if not name:
            self.logger.error("InferenceService metadata.name missing.")
            return False

        # If you provide a different namespace in the deployment I will honor it I guess..
        self.namespace = obj.get("metadata", {}).get("namespace", self.namespace)

        labels = meta.setdefault("labels", {})
        labels.setdefault("app", "semoss")
        labels["semoss_id"] = semoss_id
        annotations = meta.setdefault("annotations", {})
        annotations.setdefault("managed-by", "fastapi-kserve-launcher")

        try:
            self._ensure_inferenceservice(obj)
        except ApiException as e:
            self.logger.exception(f"KServe apply failed: {e}")
            return False

        if wait:
            return self._wait_ready(name=name)
        return True

    async def delete_inference_service(
        self,
        name: str,
        namespace: str = None,
        wait: bool = True,
        timeout_sec: int = 300,
        poll_sec: int = 3,
    ) -> bool:
        """
        Delete an InferenceService, equivalent to:
            kubectl delete inferenceservice <name> -n <namespace>

        If wait=True, block until the resource is actually gone (404).
        """
        ns = namespace or self.namespace

        self.logger.info(f"Deleting InferenceService {name} in ns {ns}")
        try:
            self.custom.delete_namespaced_custom_object(
                group=self.KServe_GROUP,
                version=self.KServe_VERSION,
                namespace=ns,
                plural=self.KServe_PLURAL,
                name=name,
            )
        except ApiException as e:
            if e.status == 404:
                self.logger.warning(
                    f"InferenceService {name} in ns {ns} not found; "
                    "treating as already deleted"
                )
                return True
            self.logger.exception(f"Failed to delete InferenceService {name}: {e}")
            return False

        if not wait:
            return True

        return self._wait_deleted(
            name=name,
            namespace=ns,
            timeout_sec=timeout_sec,
            poll_sec=poll_sec,
        )

    def list_http_routes(
        self,
        namespace: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> List[HTTPRouteInfo]:
        group = "gateway.networking.k8s.io"
        version = "v1"
        plural = "httproutes"

        effective_ns = namespace if namespace is not None else self.namespace
        effective_hostname = hostname if hostname is not None else self.hostname

        try:
            self.logger.info(
                f"Listing HTTPRoute resources in namespace '{effective_ns}'"
            )
            resp = self.custom.list_namespaced_custom_object(
                group=group,
                version=version,
                namespace=effective_ns,
                plural=plural,
            )
        except ApiException as e:
            self.logger.exception(f"Failed to list HTTPRoute resources: {e}")
            return []

        items = resp.get("items", []) or []
        routes: List[HTTPRouteInfo] = []

        for item in items:
            metadata = item.get("metadata", {}) or {}
            spec = item.get("spec", {}) or {}

            route_name = metadata.get("name")
            route_ns = metadata.get("namespace")

            hostnames = spec.get("hostnames", []) or []
            if effective_hostname:
                if effective_hostname not in hostnames:
                    self.logger.debug(
                        f"Skipping HTTPRoute {route_ns}/{route_name} "
                        f"because its hostnames {hostnames} do not include "
                        f"{effective_hostname}"
                    )
                    continue

            paths_set = set()
            for rule in spec.get("rules", []) or []:
                for match in rule.get("matches", []) or []:
                    path_obj = match.get("path") or {}
                    value = path_obj.get("value")
                    if value:
                        paths_set.add(value)

            paths_list = sorted(paths_set)
            self.logger.info(
                f"HTTPRoute {route_ns}/{route_name} "
                f"hostnames={hostnames or '<none>'} "
                f"paths={', '.join(paths_list) if paths_list else '<no paths>'}"
            )
            routes.append(
                HTTPRouteInfo(name=route_name, namespace=route_ns, paths=paths_list)
            )

        return routes
