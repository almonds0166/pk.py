
from dataclasses import dataclass
from string import ascii_lowercase as ALPHABET
from enum import Enum
from datetime import datetime, timedelta, tzinfo
import re
from typing import (
    Any,
    Union, Optional,
    Tuple, List, Set, Sequence, Dict,
    Generator,
)

import pytz
import colour
from .errors import *

# Enums

class Privacy(Enum):
    """Represents the privacies accepted by PluralKit.
    """
    PUBLIC = "public"
    PRIVATE = "private"
    #UNKNOWN = None # legacy, effectively resets privacy to "public"

# Base class for all models

class Model:
    """Base class for all models.
    """

    def json(self):
        """Return a JSON object representing this model.
        """
        model = {}
        for k, v in self.__dict__.items:
            if not k.startswith("_"):
                if hasattr(v, "json"):
                    # recurse
                    model[k] = v.json()

        return model

# IDs

class PluralKitId(Model):
    """Base class for PluralKit IDs
    """
    uuid: Optional[str]
    id: Optional[str]

    __slots__ = ["uuid", "id"]

    def _check_id(self, id):
        assert len(id) == 5 and all(c in ALPHABET for c in id), \
            f"{self.CONTEXT} ID should be a five-character lowercase string"

    def __init__(self, uuid=None, id=None):
        if uuid is None and id is None:
            raise ValueError(f"{self.CONTEXT} ID object must include at least one of: uuid, id")

        if id is not None: self._check_id(id)

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "uuid", uuid)

    def __setattr__(self, name, value):
        msg = f"cannot assign to field {name!r}"
        raise AttributeError(msg)

    def __str__(self):
        return f"{self.uuid}" if self.uuid is not None else f"{self.id}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.uuid!r}, {self.id!r})"

    json = __str__

class MemberId(PluralKitId):
    """Member IDs
    """
    CONTEXT = "Member"

class SystemId(PluralKitId):
    """System IDs
    """
    CONTEXT = "System"

class GroupId(PluralKitId):
    """Group IDs
    """
    CONTEXT = "Group"

class SwitchId(PluralKitId):
    """Switch IDs

    Switches don't have five-letter IDs, so this must be given the switch UUID.
    """
    uuid: str
    CONTEXT = "Switch"
    __slots__ = ["uuid"]

    def __init__(self, uuid):
        if uuid is None:
            raise ValueError(f"{self.CONTEXT} ID object must include uuid")

        object.__setattr__(self, "uuid", uuid)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.uuid!r})"

# Primitives

class Color(colour.Color, Model):
    """Represents a color.

    This class is initialized in the same way that a `colour.Color`_ object is. It may also take a
    `colour.Color`_ object directly.
    
    .. _`colour.Color`: https://pypi.org/project/colour/#instantiation
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0:
            args = args[0]
            if isinstance(arg, colour.Color):
                colour.Color.__init__(self, args[0].hex_l)
            elif isinstance(arg, str):
                # add octothorp to string if not there
                pattern = r"^([A-Fa-f0-9]{6})$"
                if re.search(pattern, arg):
                    arg = "#" + arg
                colour.Color.__init__(self, arg)
            return

        colour.Color.__init__(self, *args, *kwargs)

    def __str__(self):
        return self.hex_l[1:]

    json = __str__

class Timestamp(Model):
    """Represents a PluralKit UTC timestamp.

    This class works by wrapping around a `datetime` object. To access it, use ``ts.datetime``, for
    any `Timestamp` ``ts``.

    This class may be initialized in the same way that a `datetime` object is. It may also take a
    `datetime` object directly.
    """
    def __init__(self, dt: Optional[datetime]=None, *,
        year: Optional[int]=None,
        month: Optional[int]=None,
        day: Optional[int]=None,
        hour: int=0,
        minute: int=0,
        second: int=0,
        microsecond: int=0
    ):
        if dt is None and any(arg is None for arg in (year, month, day)):
            msg = (
                f"{self.__class__.__name__} is missing required arguments. Either provide a "
                f"datetime.datetime or ISO 8601 formatted string via the first positional "
                f"argument, or provide the year, month, and day through the respective keyword "
                f"arguments."
            )
            raise TypeError(msg)

        if dt is not None:
            if isinstance(dt, datetime):
                if dt.tzinfo is not None:
                    self.datetime = dt.astimezone(pytz.utc)
                else:
                    self.datetime = dt.replace(tzinfo=pytz.utc)
            elif isinstance(dt, str):
                self.datetime = datetime.strptime(bd, r"%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                msg = (
                    f"{self.__class__.__name__} takes either a datetime.datetime object or "
                    f"ISO 8601 formatted string as the first positional argument. Given "
                    f"type(dt)={type(dt)!r}"
                )
                raise TypeError(msg)

        else:
            self.datetime = datetime(year, month, day, hour, minute, second, microsecond)
            self.datetime = self.datetime.replace(tzinfo=pytz.utc)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.json()}>"

    def __str__(self):
        return (
            f"{self.year:04d}-{self.month:02d}-{self.day:02d} "
            f"{self.hour:02d}:{self.minute:02d}:{self.second:02d} UTC"
        )
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.json() == other.json()
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime == other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime == other

        return NotImplemented
    
    def __ne__(self, other):
        x = self.__eq__(other)

        if x is NotImplemented:
            return NotImplemented
        else:
            return not x

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime < other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime < other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime < other

        return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime <= other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime <= other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime <= other

        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime > other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime > other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime > other

        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.datetime >= other.datetime
        elif isinstance(other, datetime):
            if other.tzinfo is None:
                return self.datetime >= other.replace(tzinfo=pytz.utc) # assume UTC
            else:
                return self.datetime >= other

        return NotImplemented

    @property
    def year(self):
        return self.datetime.year

    @year.setter
    def year(self, value):
        self.datetime = self.datetime.replace(year=value)

    @property
    def month(self):
        return self.datetime.month

    @month.setter
    def month(self, value):
        self.datetime = self.datetime.replace(month=value)

    @property
    def day(self):
        return self.datetime.day

    @day.setter
    def day(self, value):
        self.datetime = self.datetime.replace(day=value)

    @property
    def hour(self):
        return self.datetime.hour

    @hour.setter
    def hour(self, value):
        self.datetime = self.datetime.replace(hour=value)

    @property
    def minute(self):
        return self.datetime.minute

    @minute.setter
    def minute(self, value):
        self.datetime = self.datetime.replace(minute=value)

    @property
    def second(self):
        return self.datetime.second

    @second.setter
    def second(self, value):
        self.datetime = self.datetime.replace(second=value)

    @property
    def microsecond(self):
        return self.datetime.microsecond

    @microsecond.setter
    def microsecond(self, value):
        self.datetime = self.datetime.replace(microsecond=value)

    def json(self) -> str:
        """Convert this timestamp to the ISO 8601 format that PluralKit uses internally.
        """
        return (
            f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
            f"T{self.hour:02d}:{self.minute:02d}:{self.second:02d}.{self.microsecond:06d}Z"
        )

class Birthday(Timestamp):
    """Represents a birthday.
    """
    def __str__(self):
        if self.hidden_year:
            return self.datetime.strftime("%b %d")
        else:
            return self.datetime.strftime("%b %d, ") + f"{self.year:04d}"

    @property
    def hidden_year(self) -> bool:
        """Whether this birthday's year is hidden.

        If set to ``False``, sets the birthday's year to ``0001``, `which internally represents a
        hidden year in PluralKit's API`_.

        .. _`which internally represents a hidden year in PluralKit's API`:
            https://pluralkit.me/api/#member-model
        """
        return self.year in (1, 4)

    @hidden_year.setter
    def hidden_year(self, value: bool):
        if value == True:
            self.year = 1
        else:
            pass # nothing one can do ?

    @staticmethod
    def from_json(bd: str):
        """Takes in a string (as returned by the API) and returns the `Birthday`.

        Args:
            bd: The ``YYYY-MM-DD`` formatted string representing the birthdate.

        Returns:
            Birthday: The corresponding birthday.
        """
        return Birthday(datetime.strptime(bd, r"%Y-%m-%d"))

    def json(self) -> str:
        """Returns the ``YYYY-MM-DD`` formatted birthdate.
        """
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

class Timezone(Model):
    """Represents a tzdb time zone.

    This class is initialized in the same way that `pytz.timezone`_ initializes `tzinfo` objects.
    It may also take a `tzinfo` object directly.

    Hint:
        `Here is a link to a list of tz database time zones`_

    Args:
        tz (Union[str,tzinfo]): The timezone, either as a string or as a `tzinfo` (e.g. from
            `pytz.timezone`_).

    .. _`pytz.timezone`: http://pytz.sourceforge.net/
    .. _`Here is a link to a list of tz database time zones`:
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    """
    def __init__(self, tz):
        if isinstance(tz, tzinfo):
            self.tz = tz
        else:
            self.tz = pytz.timezone(tz)

    def __eq__(self, other):
        return self.tz.zone == other.tz.zone

    def __repr__(self):
        return f"{self.__class__.__name__}({self.tz.zone!r})"

    def json(self):
        """Returns the string representation of this timezone as expected by the API.
        """
        return self.tz.zone

# Settings

@dataclass
class MemberGuildSettings(Model):
    """Member settings for a specific server.

    Keyword args:
        member: The PluralKit member this set of settings pertains to.
        guild: The id of the guild (server) that applies to this member's settings.
        display_name: The member's display name in the server.
        avatar_url: The URL of the member's avatar image in the server.
    """
    member: MemberId
    guild: int
    display_name: Optional[str]
    avatar_url: Optional[str]

@dataclass
class SystemGuildSettings(Model):
    """System settings for a specific server.

    Keyword args:
        system: The PluralKit system this set of settings pertains to.
        guild: The id of the guild (server) that applies to this member's settings.
        proxying_enabled: Whether proxying is enabled in the given server.
        tag: The system's tag (appended to the server username) for the given server.
        tag_enabled: Whether or not the system tag is shown in this server.
    """
    system: SystemId
    guild: int
    proxying_enabled: bool
    tag_enabled: bool
    tag: Optional[str]

# Proxy tags

class ProxyTag(Model):
    """Represents a single PluralKit proxy tag.

    Args:
        prefix: Prefix that will enclose proxied messages.
        suffix: Suffix that will enclose proxied messages.

    Keyword args:
        proxy_tag: Dictionary representing a proxy tag. Must have at least one of ``prefix`` or
            ``suffix`` as keys. The ``prefix`` and ``suffix`` args will overrule this dict.

    Important:
        At least one of the ``suffix`` or ``prefix`` arguments must be passed.
    
    Attributes:
        prefix (Optional[str]): Prefix that will enclose proxied messages.
        suffix (Optional[str]): Suffix that will enclose proxied messages.
    """
    def __init__(self,
        prefix: Optional[str]=None,
        suffix: Optional[str]=None,
        *,
        proxy_tag: Dict[str,str],
    ):

        # FLAG: Add proxy_tag arg

        assert prefix or suffix, \
            "A valid proxy tag must have at least one of the prefix or suffix defined."
        self.prefix = prefix
        self.suffix = suffix
    
    def __eq__(self, other):
        return self.prefix == other.prefix and self.suffix == other.suffix
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        prefix = "" if not self.prefix else f"prefix={repr(self.prefix)}"
        suffix = "" if not self.suffix else f"suffix={repr(self.suffix)}"
        attrs = ",".join(a for a in (prefix, suffix) if a)
        return (
            f"{self.__class__.__name__}({attrs})"
        )

    def match(self, message: str) -> bool:
        """Determine if a given message would be proxied under this proxy tag.
        
        Args:
            message: Message to parse.
        """
        message = message.strip()
        return (True if not self.prefix else message.startswith(self.prefix)) \
            and (True if not self.suffix else message.endswith(self.suffix))

    def json(self) -> Dict[str,Optional[str]]:
        """Return the JSON object representing this proxy tag as a Python `dict`.
        """
        return {
            "prefix": self.prefix,
            "suffix": self.suffix,
        }

class ProxyTags(Model):
    """Represents a set of PluralKit proxy tags.

    Hint:
        ProxyTags objects can be iterated or indexed to yield its underlying `ProxyTag` objects.    
    
    Args:
        proxy_tags: A sequence of `ProxyTag` objects.
    """
    def __init__(self, proxy_tags: Optional[Generator[ProxyTag,None,None]]=None):
        self._proxy_tags: Tuple[ProxyTag,...]
        if proxy_tags is None:
            self._proxy_tags = tuple()
        else:
            self._proxy_tags = tuple(proxy_tags)

    def __repr__(self):
        return f"{self.__class__.__name__}<{len(self._proxy_tags)}>"

    def __iter__(self):
        for proxy_tag in self._proxy_tags:
            yield proxy_tag

    def __getitem__(self, index):
        return self._proxy_tags[index]
    
    def __eq__(self, other):
        return set(self._proxy_tags) == set(other._proxy_tags)
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def match(self, message: str) -> bool:
        """Determine if a given message would be proxied under this set of proxy tags.
        
        Args:
            message: Message to parse.
        """
        return any(proxy_tag.match(message) for proxy_tag in self)

    def json(self) -> List[Dict[str,str]]:
        """Return the JSON object representing this proxy tag as a list of Python `dict`.
        """
        return [proxy_tag.json() for proxy_tag in self]

# Member, System, Group, Switch, and Message

@dataclass
class Member(Model):
    """Represents a PluralKit system member.

    Attributes:
        id_ (str): The member's five-letter lowercase ID.
        name (str): The member's name.
        created (Timestamp): The member's creation date.
        name_privacy (Privacy): The member's name privacy.
        display_name (Optional[str]): The member's display name.
        description (Optional[str]): The member's description.
        description_privacy (Privacy): The member's description privacy.
        color (Optional[Color]): The member's color.
        birthday (Optional[Birthday]): The member's birthdate.
        birthday_privacy (Privacy): The member's birthday privacy.
        pronouns (Optional[str]): The member's pronouns.
        pronoun_privacy (Privacy): The member's pronouns privacy.
        avatar_url (Optional[str]): The member's avatar URL.
        avatar_privacy (Privacy): The member's avatar privacy.
        keep_proxy (bool): Whether the member's proxy tags remain in the proxied message (``True``)
            or not (``False``).
        metadata_privacy (Privacy): The member's metadata (eg. creation timestamp, message count,
            etc.) privacy.
        proxy_tags (ProxyTags): The member's proxy tags.
        visibility (Privacy): The visibility privacy setting of the member.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """
    id_: Optional[str]
    name: str
    created: Timestamp
    name_privacy: Privacy
    display_name: Optional[str]
    description: Optional[str]
    description_privacy: Privacy
    color: Optional[Color]
    birthday: Optional[Birthday]
    birthday_privacy: Privacy
    pronouns: Optional[str]
    pronoun_privacy: Privacy
    avatar_url: Optional[str]
    avatar_privacy: Privacy
    keep_proxy: bool
    metadata_privacy: Privacy
    proxy_tags: Optional[ProxyTags]
    visibility: Privacy

    def __str__(self):
        return self.id_
    
    def __eq__(self, other):
        return self.id_ == other.id_
    
    def __ne__(self, other):
        return not self.__eq__(other)

class System(Model):
    """Represents a PluralKit system.

    Attributes:
        id_ (`SystemId`): The system's five-character lowercase ID.
        name (Optional[str]): The name of the system.
        description (Optional[str]): The description of the system.
        tag (Optional[str]): The system's tag appended to display names.
        pronouns (Optional[str]): The system's pronouns.
        avatar_url (Optional[str]): The system's avatar URL.
        banner (Optional[str]): The (publically accessible) URL for the system's banner.
        tz (Timezone): The system's tzdb timezone.
        created (Timestamp): The system's timestamp at creation.
        description_privacy (Privacy): The system's description privacy.
        pronoun_privacy (Privacy): The system's pronouns privacy.
        member_list_privacy (Privacy): The system's member list privacy.
        group_list_privacy (Privacy): The system's group list privacy.
        front_privacy (Privacy): The system's fronting privacy.
        front_history_privacy (Privacy): The system's fronting history privacy.
        color (`Color`): The system's color.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """
    id_: SystemId
    created: Timestamp
    name: Optional[str]
    description: Optional[str]
    tag: Optional[str]
    avatar_url: Optional[str]
    tz: Timezone
    description_privacy: Privacy
    pronoun_privacy: Privacy
    member_list_privacy: Privacy
    group_list_privacy: Privacy
    front_privacy: Privacy
    front_history_privacy: Privacy
    pronouns: Optional[str]
    banner: Optional[str]
    color: Optional[Color]

    def __str__(self):
        return self.id_
    
    def __eq__(self, other):
        return self.id_ == other.id_
    
    def __ne__(self, other):
        return not self.__eq__(other)

class Group(Model):
    """Represents a PluralKit system group

    Attributes:
        id_ (`GroupId`): PluralKit group ID.
        name (str): Name of the group.
        display_name (Optional[str]): Group display name.
        description (Optional[str]): Group description.
        icon (Optional[str]): (Publically accessible) URL of group icon.
        banner (Optional[str]): (Publically accessible) URL of group banner.
        color (Optional[Color]): Group color.
    """
    id_: Optional[GroupId]
    name: str
    display_name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    banner: Optional[str]
    color: Optional[Color]
    name_privacy: Privacy
    description_privacy: Privacy
    icon_privacy: Privacy
    list_privacy: Privacy
    metadata_privacy: Privacy
    visibility: Privacy

    def __str__(self):
        return self.id_
    
    def __eq__(self, other):
        return self.id_ == other.id_

class Switch(Model):
    """Represents a switch event.

    Attributes:
        uuid (Optional[str]): Switch's unique universal identifier (uuid).
        timestamp (Timestamp): Timestamp of the switch.
        members (Union[Sequence[str],Sequence[Member]]): Members involved.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """
    def __init__(self, *,
        uuid: str,
        timestamp: Timestamp,
        members: Union[Sequence[str],Sequence[Member]]
    ):
        self.uuid = uuid
        self.timestamp = Timestamp.parse(timestamp)

        if members is None or len(members) == 0:
            self.members = []
        else:
            self.members = [member for member in members]

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.timestamp}>"
    
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    
    def __ne__(self, other):
        return not self.__eq__(other)

class Message(Model):
    """Represents a proxied message.

    Attributes:
        timestamp (Timestamp): Timestamp of the message.
        id_ (int): The ID of the Discord message sent by the webhook.
        original (int): The ID of the (presumably deleted) original Discord message sent by the
            account.
        sender (int): The user ID of the account that sent the message.
        channel (int): The ID of the channel the message was sent to.
        system (System): The system that proxied the message.
        member (Member): The member that proxied the message.

    .. _`datetime`: https://docs.python.org/3/library/datetime.html#datetime-objects
    """
    def __init__(self, *,
        timestamp: Timestamp,
        id_: int,
        original: int,
        sender: int,
        channel: int,
        system: System,
        member: Member
    ):
        self.id_ = id_
        self.original = int(original)
        self.sender = int(sender)
        self.channel = int(channel)
        self.system = system
        self.member = member

        self.timestamp = Timestamp.parse(timestamp)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __ne__(self, other):
        return not self.__eq__(other)


