"""Load optional local credentials and invoke the resumable GFW downloader."""
import os
from pathlib import Path
from gfw_disabling import main
secret = Path(__file__).resolve().parents[1] / '.secrets/gfw.env'
if secret.exists():
    for line in secret.read_text(encoding='utf-8').splitlines():
        if line.startswith('GFW_API_TOKEN='):
            os.environ.setdefault('GFW_API_TOKEN', line.split('=',1)[1].strip().strip('"').strip("'"))
if __name__ == '__main__':
    main_args = __import__('sys').argv
    main_args.insert(1, 'download')
    main()
