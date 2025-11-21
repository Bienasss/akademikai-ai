#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

if __name__ == "__main__":
    import uvicorn
    from backend.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
