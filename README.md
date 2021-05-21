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

You can also use YAML to configure check. Try `python periscope.py -f example.yaml`.
