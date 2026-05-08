import subprocess
import pytest

PROJECT = "doc-mgmt-platform"

def nc_test(network, host, port, timeout=3):
    """
    Retorna True se a ligação foi bem sucedida.
    Retorna False se falhou OU se deu timeout (ligação bloqueada).
    """
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", f"{PROJECT}_{network}",
                "nicolaka/netshoot",
                "sh", "-c", f"nc -zv -w{timeout} {host} {port}"
            ],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        # Timeout = ligação bloqueada = comportamento esperado para testes de bloqueio
        return False

def curl_test(network, url, timeout=3):
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--network", f"{PROJECT}_{network}",
                "nicolaka/netshoot",
                "sh", "-c", f"curl -s --max-time {timeout} {url}"
            ],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def host_nc_test(host, port, timeout=3):
    try:
        result = subprocess.run(
            ["sh", "-c", f"nc -zv -w{timeout} {host} {port}"],
            capture_output=True, text=True,
            timeout=timeout + 5
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


# ─────────────────────────────────────────────────────────────
# Comunicação PERMITIDA
# ─────────────────────────────────────────────────────────────

class TestAllowedConnections:

    def test_nginx_to_flask(self):
        """nginx (private_flask) → Flask porta 8000: DEVE funcionar."""
        assert nc_test("private_flask", "web", 8000), \
            "nginx não consegue chegar ao Flask na porta 8000"

    def test_flask_to_db(self):
        """Flask (private_db) → DB porta 5432: DEVE funcionar."""
        assert nc_test("private_db", "db", 5432), \
            "Flask não consegue chegar à DB na porta 5432"

    def test_host_to_nginx_80(self):
        """Host → nginx porta 80: DEVE funcionar."""
        assert host_nc_test("localhost", 80), \
            "Porta 80 não acessível no host"

    def test_host_to_nginx_443(self):
        """Host → nginx porta 443: DEVE funcionar."""
        assert host_nc_test("localhost", 443), \
            "Porta 443 não acessível no host"


# ─────────────────────────────────────────────────────────────
# Comunicação BLOQUEADA (violações de segmentação)
# ─────────────────────────────────────────────────────────────

class TestBlockedConnections:

    def test_public_cannot_reach_flask(self):
        """Rede public NÃO deve chegar ao Flask diretamente."""
        assert not nc_test("public", "web", 8000), \
            "VIOLAÇÃO: rede public consegue chegar ao Flask!"

    def test_public_cannot_reach_db(self):
        """Rede public NÃO deve chegar à DB."""
        assert not nc_test("public", "db", 5432), \
            "VIOLAÇÃO: rede public consegue chegar à DB!"

    def test_flask_network_cannot_reach_db(self):
        """Rede private_flask NÃO deve chegar à DB."""
        assert not nc_test("private_flask", "db", 5432), \
            "VIOLAÇÃO: private_flask consegue chegar à DB!"

    def test_db_network_cannot_reach_nginx(self):
        """Rede private_db NÃO deve chegar ao nginx."""
        assert not nc_test("private_db", "nginx-web", 443), \
            "VIOLAÇÃO: private_db consegue chegar ao nginx!"

    def test_host_cannot_reach_db(self):
        """Host NÃO deve conseguir chegar à DB (porta 5432 não exposta)."""
        assert not host_nc_test("localhost", 5432), \
            "VIOLAÇÃO: porta 5432 está exposta no host!"

    def test_host_cannot_reach_flask_directly(self):
        """Host NÃO deve conseguir chegar ao Flask diretamente."""
        assert not host_nc_test("localhost", 8000), \
            "VIOLAÇÃO: porta 8000 do Flask está exposta no host!"


# ─────────────────────────────────────────────────────────────
# Isolamento da Internet (internal: true)
# ─────────────────────────────────────────────────────────────

class TestInternetIsolation:

    def test_private_flask_no_internet(self):
        """Rede private_flask NÃO deve ter acesso à internet."""
        assert not curl_test("private_flask", "https://1.1.1.1"), \
            "VIOLAÇÃO: private_flask tem acesso à internet!"

    def test_private_db_no_internet(self):
        """Rede private_db NÃO deve ter acesso à internet."""
        assert not curl_test("private_db", "https://1.1.1.1"), \
            "VIOLAÇÃO: private_db tem acesso à internet!"