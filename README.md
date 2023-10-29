# simple-irc-log-web-server

Quick and dirty IRC logging app with daily rotating logs and a web server.

## Getting Started

### 1. Domain Name and Hosting Service
- Register for an account on [Cloudflare](https://cloudflare.com)
- Get a domain name from [Freenom](https://freenom.com) (free) or [Namecheap](https://namecheap.com) (paid)
- Add the domain name to Cloudflare  and pair the nameservers to your free/paid domain
- Sign up for [Vultr](https://vultr.com)
  - Deploy server
  - Cloud Compute
  - Intel Regular Performance
  - Pick a location
  - Choose $5 tier with Debian 11
- Go back to Cloudflare and create an (A) DNS record
- Type `@` for Name, enter your server's IP address under IPv4
- Save the DNS record

### 2. VPS Setup

#### Change your password
- Connect to your new VPS server
- Type `passwd` and follow the prompts. You won't be able to see yourself typing so don't mess it up! You'll lock yourself out

#### Enable Firewall
```
ufw allow ssh
ufw allow 8000
ufw enable
```

#### Install Docker + Compose
```
# docker
apt update && apt upgrade -y
apt install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
apt update && apt install -y docker-ce
service docker start

# docker-compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### Launch
- `cd /opt && git clone https://github.com/as-helios/simple-irc-log-web-server.git && cd simple-irc-log-web-server`
- Rename `./data/irc.sample.json` and `./data/channels.sample.json`, add a nick and some channels

  Example of `irc.json`
    ```
    {
      "nick": "Atropa-Logger",
      "password": "",
      "server": "irc.oftc.net",
      "port": 6697,
      "ssl": true
    }
    ```

  Example of `channels.json`
    ```
    [
      "#atropa_logged"
    ]
    ```
- Open `docker-compose.yml` and change `SUB.YOURDOMAIN.TLD` and `YOURDOMAIN.TLD` to the domain name you have setup on Cloudflare
- Type `docker-compose up -d`
