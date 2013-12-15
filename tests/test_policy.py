import datetime
import operator
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc
from nose.tools import eq_, raises, assert_not_equal

from .context import mcbackup
from mcbackup import meta
from mcbackup.policy import RetentionPolicy, RetentionRule, Duration, DurationForever, parser, tagger

def test_durations_equals():
    eq_(Duration(relativedelta(days=7)), Duration(relativedelta(days=7)))
    eq_(DurationForever(), DurationForever())

    assert_not_equal(DurationForever(), Duration(relativedelta(days=7)))
    assert_not_equal(Duration(relativedelta(days=7)), Duration(relativedelta(months=1)))


def test_parse_snapshot():
    policy = parser.parse(["keep for 7 days"])

    eq_(policy, RetentionPolicy([RetentionRule(tagger.SnapshotTagger(), _create_duration(days=7))]))

def test_parse_tags():
    test_data = [('hourly', tagger.HourlyTagger, True),
        ('daily', tagger.DailyTagger, True),
        ('weekly', tagger.WeeklyTagger, True),
        ('monthly', tagger.MonthlyTagger, True),
        ('yearly', tagger.YearlyTagger, True),
        ('hourly', tagger.HourlyTagger, False),
        ('daily', tagger.DailyTagger, False),
        ('weekly', tagger.WeeklyTagger, False),
        ('monthly', tagger.MonthlyTagger, False),
        ('yearly', tagger.YearlyTagger, False)]

    for tag, tagger_cls, latest in test_data:
        yield _run_parse_tag, tag, tagger_cls, latest

def _run_parse_tag(tag, tagger_cls, latest):
    policy = parser.parse(["{} {} keep for 7 days".format("latest" if latest else "oldest", tag)])

    eq_(policy, RetentionPolicy([RetentionRule(tagger_cls(latest), _create_duration(days=7))]))

def test_parse_keep_duration():
    test_data = [('3600 second', _create_duration(seconds=3600)),
                 ('1800 second', _create_duration(seconds=1800)),
                 ('30 minute', _create_duration(minutes=30)),
                 ('60 minutes', _create_duration(minutes=60)),
                 ('1 hour', _create_duration(hours=1)),
                 ('3 hours', _create_duration(hours=3)),
                 ('1 day', _create_duration(days=1)),
                 ('30 days', _create_duration(days=30)),
                 ('1 week', _create_duration(weeks=1)),
                 ('8 weeks', _create_duration(weeks=8)),
                 ('1 month', _create_duration(months=1)),
                 ('6 months', _create_duration(months=6)),
                 ('1 year', _create_duration(years=1)),
                 ('4 years', _create_duration(years=4)),
                 ('forever', DurationForever())]
    for value, unit in test_data:
        yield _run_parse_keep_duration, value, unit

def _run_parse_keep_duration(parse_str, duration):
    policy = parser.parse(["keep for {}".format(parse_str)])

    eq_(policy, RetentionPolicy([RetentionRule(tagger.SnapshotTagger(), duration)]))


def test_parse_multiple_rules():
    policy = parser.parse(["keep 7 days", "latest weekly keep 1 month", "latest monthly keep 6 months"])

    eq_(policy, RetentionPolicy([
        RetentionRule(tagger.SnapshotTagger(), _create_duration(days=7)),
        RetentionRule(tagger.WeeklyTagger(True), _create_duration(months=1)),
        RetentionRule(tagger.MonthlyTagger(True), _create_duration(months=6))
    ]))

@raises(ValueError)
def test_out_of_order_rules():
    RetentionPolicy([
        RetentionRule(tagger.WeeklyTagger(True), _create_duration(months=1)),
        RetentionRule(tagger.SnapshotTagger(), _create_duration(days=7)),
        RetentionRule(tagger.MonthlyTagger(True), _create_duration(months=6))
    ])

def test_tagger_ordinals():
    taggers = [tagger.SnapshotTagger(), tagger.HourlyTagger(True), tagger.DailyTagger(True), tagger.WeeklyTagger(True),
               tagger.MonthlyTagger(True), tagger.YearlyTagger(True)]

    for (i, tagger1) in enumerate(taggers):
        for (j, tagger2) in enumerate(taggers):
            yield _run_compare_ordinals, tagger1, tagger2, i > j

def test_policy_apply():
    time_two_hour_ago = _create_past_time(hours=2).replace(second=0, microsecond=0)

    backups = {}
    create_backup(backups, "snapshot1", _create_past_time(minutes=30), meta.TAG_SNAPSHOT)
    create_backup(backups, "snapshot2", time_two_hour_ago.replace(minute=45), meta.TAG_SNAPSHOT)
    create_backup(backups, "snapshot3", time_two_hour_ago.replace(minute=30), meta.TAG_SNAPSHOT)
    create_backup(backups, "snapshot4", time_two_hour_ago.replace(minute=15), meta.TAG_SNAPSHOT)
    create_backup(backups, "snapshot5", _create_past_time(months=4), meta.TAG_SNAPSHOT)

    create_backup(backups, "hourly1", _create_past_time(hours=5), tag=meta.TAG_HOURLY)
    create_backup(backups, "hourly2", _create_past_time(hours=23), tag=meta.TAG_HOURLY)
    create_backup(backups, "hourly3", _create_past_time(days=2), tag=meta.TAG_HOURLY)

    create_backup(backups, "daily1", _create_past_time(days=3), tag=meta.TAG_DAILY)
    create_backup(backups, "daily2", _create_past_time(days=8, minutes=10),  tag=meta.TAG_DAILY)
    create_backup(backups, "daily3", _create_past_time(days=8), tag=meta.TAG_DAILY)

    create_backup(backups, "weekly1", _create_past_time(weeks=2), tag=meta.TAG_WEEKLY)
    create_backup(backups, "weekly2", _create_past_time(weeks=3), tag=meta.TAG_WEEKLY)
    create_backup(backups, "weekly3", _create_past_time(weeks=7), tag=meta.TAG_WEEKLY)

    create_backup(backups, "monthly1", _create_past_time(months=7), tag=meta.TAG_MONTHLY)
    create_backup(backups, "monthly2", _create_past_time(months=11), tag=meta.TAG_MONTHLY)
    create_backup(backups, "monthly3", _create_past_time(months=13), tag=meta.TAG_MONTHLY)

    create_backup(backups, "yearly1", _create_past_time(years=1), tag=meta.TAG_YEARLY)
    create_backup(backups, "yearly2", _create_past_time(years=3), tag=meta.TAG_YEARLY)
    create_backup(backups, "yearly3", _create_past_time(years=4), tag=meta.TAG_YEARLY)

    policy = RetentionPolicy([RetentionRule(tagger.SnapshotTagger(), _create_duration(hours=1)),
                              RetentionRule(tagger.HourlyTagger(True), _create_duration(days=1)),
                              RetentionRule(tagger.DailyTagger(True), _create_duration(days=7)),
                              RetentionRule(tagger.WeeklyTagger(True), _create_duration(weeks=4)),
                              RetentionRule(tagger.MonthlyTagger(True), _create_duration(months=12)),
                              RetentionRule(tagger.YearlyTagger(True), _create_duration(years=2))])

    (keep, purge) = policy.apply(backups.values())

    compare_backups_list(purge, [backups["snapshot3"],
                                 backups["snapshot4"],
                                 backups["daily2"],
                                 backups["monthly3"],
                                 backups["yearly2"],
                                 backups["yearly3"]])
    compare_backups_list(keep, [backups["snapshot1"],
                                retag(backups["snapshot2"], meta.TAG_HOURLY),
                                retag(backups["snapshot5"], meta.TAG_MONTHLY),
                                backups["hourly1"],
                                backups["hourly2"],
                                retag(backups["hourly3"], meta.TAG_DAILY),
                                backups["daily1"],
                                retag(backups["daily3"], meta.TAG_WEEKLY),
                                backups["weekly1"], backups["weekly2"],
                                retag(backups["weekly3"], meta.TAG_MONTHLY),
                                backups["monthly1"],
                                backups["monthly2"],
                                backups["yearly1"]])

def create_backup(dictionary, backup_id, time, tag):
    dictionary[backup_id] = meta.BackupMeta(backup_id, time, archive_format='tar|gz', tag=tag)

def compare_backups_list(actual, expected):
    eq_(sorted(actual, key=operator.attrgetter('time')),
        sorted(expected, key=operator.attrgetter('time')))

def retag(backup, new_tag):
    return backup.retag(new_tag)

def _run_compare_ordinals(tagger1, tagger2, expect_higher):
    eq_(expect_higher, tagger1.is_higher_granularity(tagger2))

def _create_past_time(**kwargs):
    return datetime.datetime.now(tzutc()) - relativedelta(**kwargs)

def _create_duration(**kwargs):
    return Duration(relativedelta(**kwargs))
