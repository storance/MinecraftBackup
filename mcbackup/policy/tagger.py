import isoweek
import operator
from .. import meta

__all__ = ["Tagger", "SnapshotTagger", "MonthlyTagger", "HourlyTagger", "DailyTagger", "WeeklyTagger",
           "MonthlyTagger", "YearlyTagger"]

class Tagger(object):
    def __init__(self, tag, ordinal, support_retag, latest=True):
        self.tag = tag
        self.support_retag = support_retag
        self.latest = latest
        self.ordinal = ordinal

    def group_by_time(self, backups):
        grouped_backups = {}

        for backup in backups:
            key = self._grouping_key(backup)
            if key not in grouped_backups:
                grouped_backups[key] = []

            grouped_backups[key].append(backup)

        for backups_for_time in grouped_backups.values():
            backups_for_time.sort(key=operator.attrgetter("time"), reverse=self.latest)

        return grouped_backups

    def should_retag(self, candidate, grouped_backups):
        key = self._grouping_key(candidate)
        if key not in grouped_backups or candidate not in grouped_backups[key]:
            raise ValueError("candidate did not appear in the list of all backups")

        return candidate == grouped_backups[key][0]

    def _grouping_key(self, backup):
        raise NotImplementedError()

    def is_higher_granularity(self, other):
        return self.ordinal > other.ordinal

    def __eq__(self, other):
        if isinstance(other, Tagger):
            return self.tag == other.tag and self.support_retag == other.support_retag and \
                self.latest == other.latest and self.ordinal == other.ordinal
        return False

    def __repr__(self):
        return "{}{{tag={},support_retag={},latest={}}}".format(self.__class__.__name__,
                                                                self.tag,
                                                                self.support_retag,
                                                                self.latest)

class SnapshotTagger(Tagger):
    def __init__(self):
        super(SnapshotTagger, self).__init__(meta.TAG_SNAPSHOT, 0, False, True)

    def should_retag(self, candidate, grouped_backups):
        return False

    def _grouping_key(self, backup):
        return backup.time

class HourlyTagger(Tagger):
    def __init__(self, latest=True):
        super(HourlyTagger, self).__init__(meta.TAG_HOURLY, 10, True, latest)

    def _grouping_key(self, backup):
        return backup.time.replace(minute=0, second=0, microsecond=0)

class DailyTagger(Tagger):
    def __init__(self, latest=True):
        super(DailyTagger, self).__init__(meta.TAG_DAILY, 20, True, latest)

    def _grouping_key(self, backup):
        return backup.time.date()

class WeeklyTagger(Tagger):
    def __init__(self, latest=True):
        super(WeeklyTagger, self).__init__(meta.TAG_WEEKLY, 30, True, latest)

    def _grouping_key(self, backup):
        (year, week, _) = backup.time.isocalendar()

        return isoweek.Week(year, week).monday()

class MonthlyTagger(Tagger):
    def __init__(self, latest=True):
        super(MonthlyTagger, self).__init__(meta.TAG_MONTHLY, 40, True, latest)

    def _grouping_key(self, backup):
        return backup.time.date().replace(day=1)

class YearlyTagger(Tagger):
    def __init__(self, latest=True):
        super(YearlyTagger, self).__init__(meta.TAG_YEARLY, 50, True, latest)

    def _grouping_key(self, backup):
        return backup.time.date().replace(month=1, day=1)
