from pathlib import Path
from Utils.Base import ReadConfig
from App.Controller import BotRunner
from loguru import logger
import sys
import elara

logger.remove()
handler_id = logger.add(sys.stderr, level="INFO")
logger.add(sink='run.log',
           format="{time} - {level} - {message}",
           level="INFO",
           rotation="20 MB",
           enqueue=True)
db = elara.exe(path=f"{str(Path.cwd())}/Config/db.db", commitdb=True)
config = ReadConfig().parse_file(str(Path.cwd()) + "/Config/app.toml")
App = BotRunner(config, db)
App.run()
