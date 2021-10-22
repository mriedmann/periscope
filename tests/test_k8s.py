import json
import random
import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import kubernetes
from kubernetes.client.api.custom_objects_api import CustomObjectsApi
from kubernetes.client.exceptions import ApiException
from kubernetes.config import ConfigException
from parameterized import parameterized

from pipecheck.k8s import K8sPipecheckCheck, K8sPipecheckRepository, get_config_from_kubernetes


def generate_cr(namespace, name, spec):
    created = datetime.now() + timedelta(minutes=random.randint(-600, 600))
    return {
        "apiVersion": "pipecheck.r3i.at/v1alpha1",
        "kind": "Check",
        "metadata": {
            "creationTimestamp": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "generation": random.randint(1, 100),
            "name": name,
            "namespace": namespace,
            "resourceVersion": random.randint(100000, 9999999),
            "uid": str(uuid.uuid4()),
        },
        "spec": spec,
    }


class K8sPipecheckCheckTests(unittest.TestCase):
    def test_init_json(self):
        spec = {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}}
        cr = generate_cr("test", "pipecheck-sample", spec)
        j = json.dumps(cr)
        check = K8sPipecheckCheck(json=j)
        self.assertEqual(check.name, "pipecheck-sample")
        self.assertEqual(check.namespace, "test")
        self.assertDictEqual(check.spec, spec)

    def test_init_invalid(self):
        self.assertRaises(ValueError, K8sPipecheckCheck)

    def test_str(self):
        spec = {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}}
        cr = generate_cr("test", "pipecheck-sample", spec)
        j = json.dumps(cr)
        check = K8sPipecheckCheck(json=j)
        expected_str = f"K8sPipecheckCheck(json='{j}')"
        self.assertEqual(expected_str, str(check))


class K8sPipecheckRepositoryTests(unittest.TestCase):
    @parameterized.expand(
        [
            (
                "test",
                "app==test",
                [
                    generate_cr("test", "check-a", {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}}),
                    generate_cr("test", "check-b", {"b": {"host": "8.8.4.4", "port": 53, "type": "tcp"}}),
                    generate_cr("test", "check-c", {"c": {"host": "1.1.1.1", "port": 53, "type": "tcp"}}),
                ],
                [
                    K8sPipecheckCheck(generate_cr("test", "check-a", {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}})),
                    K8sPipecheckCheck(generate_cr("test", "check-b", {"b": {"host": "8.8.4.4", "port": 53, "type": "tcp"}})),
                    K8sPipecheckCheck(generate_cr("test", "check-c", {"c": {"host": "1.1.1.1", "port": 53, "type": "tcp"}})),
                ],
            ),
            (
                "test2",
                "app==test1232",
                [
                    generate_cr("test", "check-a", {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}}),
                ],
                [
                    K8sPipecheckCheck(generate_cr("test", "check-a", {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}})),
                ],
            ),
            ("test", None, [], []),
        ]
    )
    def test_get_all_checks_from_namespace(self, namespace, label_selector, items, expected_checks):
        namespace = "test"
        label_selector = "app==test"
        items = [
            generate_cr(namespace, "check-a", {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}}),
            generate_cr(namespace, "check-b", {"b": {"host": "8.8.4.4", "port": 53, "type": "tcp"}}),
            generate_cr(namespace, "check-c", {"c": {"host": "1.1.1.1", "port": 53, "type": "tcp"}}),
        ]
        data = {"items": items}
        expected_checks = [
            K8sPipecheckCheck(generate_cr(namespace, "check-a", {"a": {"host": "8.8.8.8", "port": 53, "type": "tcp"}})),
            K8sPipecheckCheck(generate_cr(namespace, "check-b", {"b": {"host": "8.8.4.4", "port": 53, "type": "tcp"}})),
            K8sPipecheckCheck(generate_cr(namespace, "check-c", {"c": {"host": "1.1.1.1", "port": 53, "type": "tcp"}})),
        ]
        checks = []

        with patch.object(CustomObjectsApi, "list_namespaced_custom_object", return_value=data) as mock_method:
            repo = K8sPipecheckRepository(True, CustomObjectsApi())
            checks = list(repo.get_all_checks_from_namespace(namespace, label_selector))
        mock_method.assert_called_once_with(
            group="pipecheck.r3i.at", version="v1alpha1", plural="checks", namespace=namespace, label_selector=label_selector
        )
        for i, check in enumerate(checks):
            self.assertEqual(expected_checks[i].name, check.name)
            self.assertEqual(expected_checks[i].namespace, check.namespace)
            self.assertDictEqual(expected_checks[i].spec, check.spec)

    def test_init_try_incluster_first_and_dont_use_kubeconfig_if_successful(self):
        with patch.object(kubernetes.config, "load_incluster_config") as incluster_method:
            with patch.object(kubernetes.config, "load_kube_config") as kube_method:
                K8sPipecheckRepository()
        incluster_method.assert_called_once()
        kube_method.assert_not_called()

    def test_init_try_kubeconfig_if_incluster_not_working(self):
        with patch.object(kubernetes.config, "load_incluster_config", side_effect=ConfigException()) as incluster_method:
            with patch.object(kubernetes.config, "load_kube_config") as kube_method:
                K8sPipecheckRepository()
        incluster_method.assert_called_once()
        kube_method.assert_called_once()

    def test_init_raise_if_no_config_available(self):
        with patch.object(kubernetes.config, "load_incluster_config", side_effect=ConfigException()) as incluster_method:
            with patch.object(kubernetes.config, "load_kube_config", side_effect=ConfigException()) as kube_method:
                self.assertRaises(Exception, K8sPipecheckRepository)
        incluster_method.assert_called_once()
        kube_method.assert_called_once()


class K8sTests(unittest.TestCase):
    @parameterized.expand(
        [
            (
                "without merge",
                "test",
                [
                    K8sPipecheckCheck(
                        {
                            "metadata": {"name": "test1", "namespace": "test"},
                            "spec": {
                                "cf_a": {"type": "tcp", "host": "1.1.1.1", "port": "53"},
                                "cf_b": {"type": "tcp", "host": "1.0.0.1", "port": "53"},
                            },
                        }
                    ),
                    K8sPipecheckCheck(
                        {
                            "metadata": {"name": "test2", "namespace": "test"},
                            "spec": {
                                "go_a": {"type": "tcp", "host": "8.8.8.8", "port": "53"},
                                "go_b": {"type": "tcp", "host": "8.8.4.4", "port": "53"},
                            },
                        }
                    ),
                ],
                {
                    "cf_a": {"type": "tcp", "host": "1.1.1.1", "port": "53"},
                    "cf_b": {"type": "tcp", "host": "1.0.0.1", "port": "53"},
                    "go_a": {"type": "tcp", "host": "8.8.8.8", "port": "53"},
                    "go_b": {"type": "tcp", "host": "8.8.4.4", "port": "53"},
                },
            ),
            (
                "with merge",
                "test",
                [
                    K8sPipecheckCheck(
                        {
                            "metadata": {"name": "test1", "namespace": "test"},
                            "spec": {
                                "dns_a": {"type": "tcp", "host": "1.1.1.1", "port": "53"},
                                "dns_b": {"type": "tcp", "host": "1.0.0.1", "port": "53"},
                            },
                        }
                    ),
                    K8sPipecheckCheck(
                        {
                            "metadata": {"name": "test2", "namespace": "test"},
                            "spec": {
                                "dns_a": {"type": "tcp", "host": "8.8.8.8", "port": "53"},
                                "dns_b": {"type": "tcp", "host": "8.8.4.4", "port": "53"},
                            },
                        }
                    ),
                ],
                {
                    "dns_a": {"type": "tcp", "host": "8.8.8.8", "port": "53"},
                    "dns_b": {"type": "tcp", "host": "8.8.4.4", "port": "53"},
                },
            ),
        ]
    )
    def test_get_config_from_kubernetes(self, msg, namespace, checks, expected_config):
        config = {}
        with patch.object(K8sPipecheckRepository, "get_all_checks_from_namespace", return_value=checks) as mock_method:
            config = get_config_from_kubernetes(namespace, None, K8sPipecheckRepository(no_config=True))
        mock_method.assert_called_once_with(namespace, None)
        self.assertDictEqual(expected_config, config, msg=msg)

    def test_get_all_checks_from_namespaces_no_crd_installed(self):
        with patch.object(
            K8sPipecheckRepository, "get_all_checks_from_namespace", side_effect=ApiException(status=404)
        ) as mock_method:
            self.assertRaises(Exception, get_config_from_kubernetes, "test", None, K8sPipecheckRepository(no_config=True))
        mock_method.assert_called_once()


if __name__ == "__main__":
    unittest.main()
