import sys
import webbrowser
from urllib.parse import urlencode
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('Browser')

def main():
    try:
        if len(sys.argv) < 2:
            logger.error("No client_id provided")
            sys.exit(1)
            
        client_data = sys.argv[1]
        params = {'session_id': client_data}
        url = f"http://localhost:3001?{urlencode(params)}"
        logger.info(f"Opening browser URL: {url}")
        webbrowser.open(url)
    except KeyboardInterrupt:
        logger.info("Browser launcher terminated")
    except Exception as e:
        logger.error(f"Failed to launch browser: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

