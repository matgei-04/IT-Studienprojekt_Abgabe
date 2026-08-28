"""Desktop-Anwendung SmartAssign."""

try:
    import truststore

    # httpx (von supabase-py genutzt) prüft HTTPS-Zertifikate standardmäßig nur
    # gegen das mitgelieferte certifi-Bundle, nicht gegen den echten
    # Windows-Zertifikatsspeicher. In manchen Netzwerken (z. B. mit
    # TLS-inspizierendem Firmen-/Hochschul-Proxy) führt das zu
    # SSL-Zertifikatsfehlern, obwohl Windows der Verbindung vertraut.
    # truststore lässt Python stattdessen den echten OS-Zertifikatsspeicher
    # nutzen – hier früh aktiviert, bevor irgendein HTTPS-Aufruf stattfindet.
    truststore.inject_into_ssl()
except ImportError:
    # Optional (u. a. Python < 3.10); App läuft auch ohne.
    pass
