# Periscope

This simple tool can be used to verify the state of a system's context. It is meant to be used as test or init container e.g. to make sure that all needed connections are available. 

## The name

This tool provides some insight into the current state of an environment, without actually moving into it (like with a deployment or interactive connection). This can be compared to a periscope on submarines to scout the surface without emerging. Doing so saves time, energy and reduces the risk of being shot. 

In an IT context, it means to be able to detect configurations-errors (in surrounding systems like firewalls or DNS) early to avoid problems during a deployment. 

## How to use it

Simply use the docker-image or download the script and run it directly. See `--help` for some details on the CLI. If you want to run the script locally, use `python -m pip install -r requirements.txt` to install all required libraries before you start the script.

To run tests, you have to provide 'checks' as parameters. See the following example (or the tests.py file) to get an idea:

```bash
$ python periscope.py \
  --http https://httpstat.us/200 \
  --tcp  8.8.8.8:53 \
  --ping 8.8.8.8 \
  --dns  'dns.google=8.8.8.8,8.8.4.4'
[OK]     DNS resolution for 'dns.google' successfull (8.8.8.8)
[OK]     DNS resolution for 'dns.google' returned expected ip '8.8.8.8'
[OK]     '8.8.8.8' reachable (19.462ms)
[OK]     successfully connected to tcp-port 53 on 8.8.8.8
[OK]     HTTP HEAD to 'https://httpstat.us/200' returned 200
```

Alternatively, just use the pre-built docker-image.

```bash
$ docker run --rm docker.io/mriedmann/periscope --ping 8.8.8.8
[OK]     ICMP '8.8.8.8' reachable (30.017ms)
```

### Multiple checks of same type

To define e.g. multiple ping checks, just provide a space-separated list to the `--ping` argument. 

```bash
$ python periscope.py --ping 1.1.1.1 8.8.8.8 1.0.0.1 8.8.4.4
[OK]     ICMP '1.1.1.1' reachable (21.138ms)
[OK]     ICMP '8.8.8.8' reachable (30.992ms)
[OK]     ICMP '1.0.0.1' reachable (24.709ms)
[OK]     ICMP '8.8.4.4' reachable (36.364ms)
````

### Global configuration

There are some global settings like http-method or tcp-timeout (see `python periscope.py --help`). If you need to set these settings on a per-check basis, you have to use a command-file. 

### Command File

You can also use YAML to configure checks. Try `python periscope.py -f example.yaml` or `cat example.yaml | python periscope.py -f -`.

The used file-structure is optimized for layered YAMLs, so tools like Helm or Kustomize can be used easily to template this config. Understanding the parsing-method is easy: All paths are searched till a `type` key is found. All keys on the same level are considered config-keys. These keys will be used as named-argument for type-named checks (see `checks.py` for possibilities). All `type` keys will be taken into account, unless they are nested beneath a layer where a type-key was already present. These branches will be ignored. 

```yaml
a:
  a1:
    valid_check:
      type: tcp
      host: 8.8.8.8
      port: 53
      tcp_timeout: 1.0
b:
  another_valid_check:
    type: tcp
    host: 8.8.8.8
    port: 53
    ignored_check:
      type: tcp
      host: 8.8.8.8
      port: 53
```

Commandline arguments will be taken into account. This is can be used to define global config parameters like tcp-timeout.

### Remote use

Using stdin with `-f -` as input gives you the possibility to pipe a local commandfile to a remote installation.

To execute checks against k8s just use `kubectl run`.

```bash
$ cat example.yaml | kubectl run --image=docker.io/mriedmann/periscope:latest --rm --restart=Never -i checks -- -f -
```

If you want to use a remote host with docker installed, just use `docker run`.

```bash
$ cat example.yaml | ssh $HOST 'docker run --rm -i docker.io/mriedmann/periscope:latest -f - '
```

## Checks

All currently available checks can be find in `checks.py`. If you miss any, feel free to open a feature request or PR.

### Ping

Simple ICMP echo ping check using [icmplib](https://github.com/ValentinBELYN/icmplib). On some systems this check needs minor modifications to be able to run without root previledges (see https://github.com/ValentinBELYN/icmplib#how-to-use-the-library-without-root-privileges).

### HTTP

Basic HTTP/S check using `urllib3`. If you want to check self-signed certificates you have to configure a trusted CA-Bundle. See the `--ca-certs` argument in `--help`.

### TCP

Very simple tcp-handshake check.

### DNS

Tries to resolve a given hostname (using the os defaults) and checks against provided IPs or subnets. 
