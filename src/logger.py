import logging
from datetime import datetime
from src.player import Player

logger = logging.getLogger(__name__)
logging.basicConfig(filename="chapflix.log", level=logging.INFO)


def log_app_starting() -> None:
    logger.info(f"Starting app at {datetime.now()}")


def log_user_selection(player: Player) -> None:
    logger.info(f"User {player.user_display_name} selected")


def log_file_played(player: Player) -> None:
    logger.info(f"{player.current_selection} selected")


def log_file_paused(player: Player) -> None:
    logger.info(
        f"{player.user_display_name} paused {player.current_selection} at {datetime.now()}"
    )
