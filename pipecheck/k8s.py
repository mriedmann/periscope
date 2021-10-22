import json as json_parser

from kubernetes import client, config
from kubernetes.client.api.custom_objects_api import CustomObjectsApi

from pipecheck.utils import mergedicts


class K8sPipecheckCheck:
    _data: dict
    name: str
    namespace: str
    spec: dict

    def __init__(self, d: dict = None, json: str = None):
        if d is None and json is None:
            raise ValueError("d or json argument have to be set")
        if d is None:
            d = json_parser.loads(json)
        self._data = d
        self.name = d["metadata"]["name"]
        self.namespace = d["metadata"]["namespace"]
        self.spec = d["spec"]

    def __str__(self):
        dataJson = json_parser.dumps(self._data)
        return f"K8sPipecheckCheck(json='{dataJson}')"


class K8sPipecheckRepository:
    co: CustomObjectsApi

    def __init__(self, no_config=False, co=None) -> None:
        if not no_config:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                try:
                    config.load_kube_config()
                except config.ConfigException:
                    raise Exception("Could not configure kubernetes python client")

        if co is not None:
            self.co = co
        else:
            self.co = client.CustomObjectsApi()

    def get_all_checks_from_namespace(self, namespace, label_selector=None):
        ret = self.co.list_namespaced_custom_object(
            group="pipecheck.r3i.at", version="v1alpha1", plural="checks", namespace=namespace, label_selector=label_selector
        )
        for i in ret["items"]:
            yield K8sPipecheckCheck(i)


def get_config_from_kubernetes(namespace, label_selector=None, repository=None):
    # not using default value in def to avoid class creation on import
    if repository is None:
        repository = K8sPipecheckRepository()

    config = {}
    try:
        for check in repository.get_all_checks_from_namespace(namespace, label_selector):
            config = dict(mergedicts(config, check.spec))
    except client.exceptions.ApiException as e:
        if e.status == 404:
            raise Exception("CRD not found! Please install the CDR.")
        raise e
    return config
