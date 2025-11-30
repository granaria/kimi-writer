# config.py
import os
from pathlib import Path


class ParametersONE:
    #
    # resa rational meets humpty dumpty. the cold blooded killer from the 'alice in wonderland' theme park located in tokyo
    # Auto-detected
    '''
    API_KEY = os.getenv("MOONSHOT_API_KEY")
    if not API_KEY:
        raise EnvironmentError("MOONSHOT_API_KEY not set!")

    BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")

    '''

    BACKUP_DIR = Path("backups")
    if BACKUP_DIR.exists():
        print("BACKUP_DIR exists")
    else:
        print("BACKUP_DIR does NOT exist → creating...")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Fixed, always-correct endpoint for Moonshot token estimation (as of Nov 2025)
    MOONSHOT_TOKEN_ESTIMATE_URL = "https://api.moonshot.ai/v1/tokenizers/estimate-token-count"

    VERSION = "agentONE-11.25"
    MAX_ITERATIONS = 5  # 50
    TOKEN_LIMIT = 200000  # 120_000n
    COMPRESSION_THRESHOLD = 180000  # 100_000 # Trigger compression at 90% of limit
    MAX_TOKENS:int = 65536  # 64K tokens
    MAX_TOKENS2:int = 4096
    BACKUP_INTERVAL = 50  # 5 # Save backup summary every N iterations





    agentMODEL= "kimi-k2-thinking"
    MODEL = agentMODEL  # "kimi-k2-thinking"  "moonshot-v1-128k"

    # user input
    agentDescription = "AgentONE - Create novels, books, and short stories",
    agentEpilog = ""
    
    TEMPERATURE = .7  # 1.0
    
    """
Examples:
  # Fresh start with inline prompt
  python kimi-writer.py "Create a collection of sci-fi short stories"
  
  # Recovery mode from previous context
  python kimi-writer.py --recover my_project/.context_summary_20250107_143022.md
        """