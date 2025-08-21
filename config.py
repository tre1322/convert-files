# config.py
import os

MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "50"))
RETENTION_MINUTES = int(os.getenv("RETENTION_MINUTES", "30"))

# Where all temp jobs go (Railway ephemeral disk is fine)
TMP_ROOT = os.getenv("TMP_ROOT", "/tmp/convert-jobs")
