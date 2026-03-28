import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import vk_api

logger = logging.getLogger(__name__)


class VkParser:
    def __init__(
        self,
        token: str,
        session_name: str = "vk_session",
        api_version: str = "5.199",
    ):
        self._token = token
        self._vk_session: Optional[vk_api.VkApi] = None
        self._vk = None
        self._api_version = api_version

    def _ensure_client(self) -> None:
        if self._vk is not None:
            return

        self._vk_session = vk_api.VkApi(token=self._token, api_version=self._api_version)
        self._vk = self._vk_session.get_api()
        logger.info("VK client initialized")

    async def parse(
        self,
        sources: List[Dict],
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        try:
            self._ensure_client()
            results: List[Dict] = []
            logger.info("Starting VK parsing for %d groups", len(sources))

            for source in sources:
                group_news = await self._parse_single_group(source, date_from=date_from, date_to=date_to)
                results.extend(group_news)

            return results
        except Exception as exc:
            logger.error("VK critical error: %s", exc)
            return []

    async def _parse_single_group(
        self,
        source: Dict,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        results: List[Dict] = []

        try:
            group_id = self._extract_group_identifier(source["source_link"])
            last_date = self._to_date(source.get("last_message_date"))

            start_date = self._to_date(date_from)
            end_date = self._to_date(date_to)

            # If explicit date_from is not provided, use DB date boundary as before.
            lower_bound = start_date if start_date is not None else last_date
            inclusive_start = start_date is not None

            params = {
                "count": 50,
                "offset": 0,
                "filter": "owner",
            }

            if group_id.isdigit():
                params["owner_id"] = -int(group_id)
            else:
                params["domain"] = group_id

            for _ in range(2):
                response = self._vk.wall.get(**params)
                items = response.get("items", [])
                if not items:
                    break

                stop = False
                for post in items:
                    if post.get("is_pinned"):
                        continue

                    post_dt = datetime.fromtimestamp(post["date"])
                    post_date = post_dt.date()

                    if end_date and post_date > end_date:
                        continue

                    if lower_bound is not None:
                        if inclusive_start:
                            if post_date < lower_bound:
                                stop = True
                                break
                        else:
                            if post_date <= lower_bound:
                                stop = True
                                break

                    text = (post.get("text") or "").strip()
                    if not text:
                        continue

                    clean_text = " ".join(text.split())
                    results.append(
                        {
                            "source_name": source["source_name"],
                            "source_link": source["source_link"],
                            "contact": source.get("contact"),
                            "date": post_dt.strftime("%Y-%m-%d"),
                            "message": clean_text,
                        }
                    )

                if stop:
                    break

                params["offset"] += params["count"]

        except Exception as exc:
            logger.error("VK parsing error in group %s: %s", source.get("source_name"), exc)

        return results

    async def disconnect(self) -> None:
        logger.info("VkParser disconnect called")

    @staticmethod
    def _extract_group_identifier(url: str) -> str:
        last = url.rstrip("/").split("/")[-1]
        if last.startswith("public"):
            return last[6:]
        if last.startswith("club"):
            return last[4:]
        return last

    @staticmethod
    def _to_date(value) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
                try:
                    return datetime.strptime(text, fmt).date()
                except ValueError:
                    continue
        return None
