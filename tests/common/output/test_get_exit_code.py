import argparse
import os
import unittest
from unittest import mock

from checkov.common.bridgecrew.check_type import CheckType
from checkov.common.bridgecrew.code_categories import CodeCategoryType, CodeCategoryConfiguration
from checkov.common.bridgecrew.integration_features.features.repo_config_integration import \
    integration as repo_config_integration
from checkov.common.bridgecrew.severities import BcSeverities, Severities
from checkov.common.models.enums import CheckResult
from checkov.common.output.report import Report
from checkov.common.output.record import Record
from checkov.common.runners.runner_registry import RunnerRegistry
from checkov.common.util.consts import PARSE_ERROR_FAIL_FLAG
from checkov.runner_filter import RunnerFilter


class TestGetExitCode(unittest.TestCase):

    def test_get_exit_code(self):
        record1 = Record(check_id='CKV_AWS_157',
                         bc_check_id='BC_AWS_157',
                         check_name="Some RDS check", check_result={"result": CheckResult.FAILED},
                         code_block=None, file_path="./rds.tf",
                         file_line_range='1:3',
                         resource='aws_db_instance.sample', evaluations=None,
                         check_class=None, file_abs_path=',.',
                         severity=Severities[BcSeverities.LOW],
                         entity_tags={
                             'tag1': 'value1'
                         })
        record2 = Record(check_id='CKV_AWS_16',
                         bc_check_id='BC_AWS_16',
                         check_name="Another RDS check",
                         check_result={"result": CheckResult.FAILED},
                         code_block=None, file_path="./rds.tf",
                         file_line_range='1:3',
                         resource='aws_db_instance.sample', evaluations=None,
                         check_class=None, file_abs_path=',.',
                         severity=Severities[BcSeverities.HIGH],
                         entity_tags={
                             'tag1': 'value1'
                         })

        record3 = Record(check_id='CKV_AWS_161',
                         bc_check_id='BC_AWS_161',
                         check_name="Another RDS check",
                         check_result={"result": CheckResult.PASSED},
                         code_block=None, file_path="./rds.tf",
                         file_line_range='1:3',
                         resource='aws_db_instance.sample', evaluations=None,
                         check_class=None, file_abs_path=',.',
                         severity=Severities[BcSeverities.LOW],
                         entity_tags={
                             'tag1': 'value1'
                         })
        record4 = Record(check_id='CKV_AWS_118',
                         bc_check_id='BC_AWS_118',
                         check_name="Another RDS check",
                         check_result={"result": CheckResult.PASSED},
                         code_block=None, file_path="./rds.tf",
                         file_line_range='1:3',
                         resource='aws_db_instance.sample', evaluations=None,
                         check_class=None, file_abs_path=',.',
                         severity=Severities[BcSeverities.HIGH],
                         entity_tags={
                             'tag1': 'value1'
                         })

        r = Report("terraform")
        r.add_record(record1)
        r.add_record(record2)
        r.add_record(record3)
        r.add_record(record4)

        OFF = Severities[BcSeverities.OFF]
        LOW = Severities[BcSeverities.LOW]
        MEDIUM = Severities[BcSeverities.MEDIUM]
        HIGH = Severities[BcSeverities.HIGH]
        CRITICAL = Severities[BcSeverities.CRITICAL]

        # When soft_fail=True, the exit code should always be 0 if there are no other soft/hard fail exceptions.
        test_default = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        test_soft_fail = r.get_exit_code({'soft_fail': True, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        test_hard_fail_off = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': OFF})

        # When soft_fail_on=['check1', 'check2'], exit code should be 0 if the only failing checks are in the soft_fail_on list
        positive_test_soft_fail_on_code = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_AWS_157', 'CKV_AWS_16'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        positive_test_soft_fail_on_code_one_sev = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_AWS_16'], 'soft_fail_threshold': LOW, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        positive_test_soft_fail_on_code_thresh = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': HIGH, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        positive_test_soft_fail_on_code_bc_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['BC_AWS_157', 'BC_AWS_16'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})

        negative_test_soft_fail_on_code = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_AWS_157'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        negative_test_soft_fail_on_code_thresh = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': LOW, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        negative_test_soft_fail_on_code_bc_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['BC_AWS_157'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})

        positive_test_soft_fail_on_wildcard_code = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_AWS*'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        positive_test_soft_fail_on_wildcard_code_bc_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['BC_AWS*'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})

        negative_test_soft_fail_on_wildcard_code = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_OTHER*'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})
        negative_test_soft_fail_on_wildcard_code_bc_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['BC_OTHER*'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': None})

        # When hard_fail_on=['check1', 'check2'], exit code should be 1 if any checks in the hard_fail_on list fail
        positive_test_hard_fail_on_code = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': ['CKV_AWS_157'], 'hard_fail_threshold': None})
        positive_test_hard_fail_on_code_one_sev = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': LOW})
        positive_test_hard_fail_on_code_bc_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': ['BC_AWS_157'], 'hard_fail_threshold': None})

        negative_test_hard_fail_on_code = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': ['CKV_AWS_161', 'CKV_AWS_118'], 'hard_fail_threshold': None})
        negative_test_hard_fail_on_code_bc_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': [], 'soft_fail_threshold': None, 'hard_fail_checks': ['BC_AWS_161', 'BC_AWS_118'], 'hard_fail_threshold': None})

        combined_test_soft_fail_sev_hard_fail_id = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_AWS_16'], 'soft_fail_threshold': LOW, 'hard_fail_checks': ['CKV_AWS_157'], 'hard_fail_threshold': None})
        combined_test_soft_fail_id_hard_fail_sev = r.get_exit_code({'soft_fail': False, 'soft_fail_checks': ['CKV_AWS_16'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': HIGH})
        combined_test_soft_fail_id_hard_fail_sev_fail = r.get_exit_code({'soft_fail': True, 'soft_fail_checks': ['CKV_AWS_16'], 'soft_fail_threshold': None, 'hard_fail_checks': [], 'hard_fail_threshold': HIGH})

        self.assertEqual(test_default, 1)
        self.assertEqual(test_soft_fail, 0)
        self.assertEqual(test_hard_fail_off, 0)
        self.assertEqual(positive_test_soft_fail_on_code, 0)
        self.assertEqual(positive_test_soft_fail_on_code_one_sev, 0)
        self.assertEqual(positive_test_soft_fail_on_code_thresh, 0)
        self.assertEqual(positive_test_soft_fail_on_code_bc_id, 0)
        self.assertEqual(negative_test_soft_fail_on_code, 1)
        self.assertEqual(negative_test_soft_fail_on_code_thresh, 1)
        self.assertEqual(negative_test_soft_fail_on_code_bc_id, 1)

        self.assertEqual(positive_test_soft_fail_on_wildcard_code, 0)
        self.assertEqual(positive_test_soft_fail_on_wildcard_code_bc_id, 0)
        self.assertEqual(negative_test_soft_fail_on_wildcard_code, 1)
        self.assertEqual(negative_test_soft_fail_on_wildcard_code_bc_id, 1)

        self.assertEqual(positive_test_hard_fail_on_code, 1)
        self.assertEqual(positive_test_hard_fail_on_code_one_sev, 1)
        self.assertEqual(positive_test_hard_fail_on_code_bc_id, 1)
        self.assertEqual(negative_test_hard_fail_on_code, 0)
        self.assertEqual(negative_test_hard_fail_on_code_bc_id, 0)

        self.assertEqual(combined_test_soft_fail_sev_hard_fail_id, 1)
        self.assertEqual(combined_test_soft_fail_id_hard_fail_sev, 1)
        self.assertEqual(combined_test_soft_fail_id_hard_fail_sev_fail, 0)

        with mock.patch.dict(os.environ, {PARSE_ERROR_FAIL_FLAG: "true"}):
            r.add_parsing_error("some_file.tf")
            self.assertEqual(
                r.get_exit_code(
                    {
                        "soft_fail": False,
                        "soft_fail_checks": [],
                        "soft_fail_threshold": None,
                        "hard_fail_checks": [],
                        "hard_fail_threshold": None,
                    }
                ),
                1,
            )

    def test_get_fail_thresholds_enforcement_rules(self):

        old_configs = repo_config_integration.code_category_configs

        repo_config_integration.code_category_configs = {
            CodeCategoryType.IAC: CodeCategoryConfiguration(CodeCategoryType.IAC, Severities[BcSeverities.MEDIUM], Severities[BcSeverities.CRITICAL])
        }
        config = argparse.Namespace(
            use_enforcement_rules=True,
            soft_fail=False,
            soft_fail_on=None,
            hard_fail_on=None
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': None,
            'hard_fail_checks': [],
            'hard_fail_threshold': Severities[BcSeverities.CRITICAL]
        }
        # the soft-fail threshold is None because we will just let it be implicit based off hard fail (this is how enforcement rules works)
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=True,
            soft_fail=True,
            soft_fail_on=None,
            hard_fail_on=None
        )
        expected = {
            'soft_fail': True,
            'soft_fail_checks': [],
            'soft_fail_threshold': None,
            'hard_fail_checks': [],
            'hard_fail_threshold': None  # soft fail ignores enforcement rules
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=True,
            soft_fail=False,
            soft_fail_on=['MEDIUM'],
            hard_fail_on=None
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': Severities[BcSeverities.MEDIUM],
            'hard_fail_checks': [],
            'hard_fail_threshold': None
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=True,
            soft_fail=False,
            soft_fail_on=['MEDIUM'],
            hard_fail_on=['HIGH']
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': Severities[BcSeverities.MEDIUM],
            'hard_fail_checks': [],
            'hard_fail_threshold': Severities[BcSeverities.HIGH]
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=True,
            soft_fail=False,
            soft_fail_on=['CKV_AWS_123'],
            hard_fail_on=['CKV_AWS_789']
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': ['CKV_AWS_123'],
            'soft_fail_threshold': None,
            'hard_fail_checks': ['CKV_AWS_789'],
            'hard_fail_threshold': Severities[BcSeverities.CRITICAL]
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        repo_config_integration.code_category_configs = {
            CodeCategoryType.IAC: CodeCategoryConfiguration(CodeCategoryType.IAC, Severities[BcSeverities.LOW], Severities[BcSeverities.OFF])
        }
        config = argparse.Namespace(
            use_enforcement_rules=True,
            soft_fail=False,
            soft_fail_on=None,
            hard_fail_on=None
        )
        expected = {
            'soft_fail': True,  # set as a global soft fail
            'soft_fail_checks': [],
            'soft_fail_threshold': None,
            'hard_fail_checks': [],
            'hard_fail_threshold': Severities[BcSeverities.OFF]
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        repo_config_integration.code_category_configs = old_configs

    def test_get_fail_thresholds_plain(self):

        config = argparse.Namespace(
            use_enforcement_rules=False,
            soft_fail=True,
            soft_fail_on=['MEDIUM', 'CKV_AWS_123'],
            hard_fail_on=['HIGH', 'CKV_AWS_789']
        )

        expected = {
            'soft_fail': True,
            'soft_fail_checks': ['CKV_AWS_123'],
            'soft_fail_threshold': Severities[BcSeverities.MEDIUM],
            'hard_fail_checks': ['CKV_AWS_789'],
            'hard_fail_threshold': Severities[BcSeverities.HIGH]
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=False,
            soft_fail=False,
            soft_fail_on=['LOW,HIGH'],
            hard_fail_on=[]
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': Severities[BcSeverities.HIGH],  # take the higher severity
            'hard_fail_checks': [],
            'hard_fail_threshold': None
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=False,
            soft_fail=False,
            soft_fail_on=[],
            hard_fail_on=['LOW,HIGH']
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': None,
            'hard_fail_checks': [],
            'hard_fail_threshold': Severities[BcSeverities.LOW]  # take the lower severity
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=False,
            soft_fail=False,
            soft_fail_on=['low'],  # case insensitive
            hard_fail_on=[]
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': Severities[BcSeverities.LOW],
            'hard_fail_checks': [],
            'hard_fail_threshold': None
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)

        config = argparse.Namespace(
            use_enforcement_rules=False,
            soft_fail=False,
            soft_fail_on=[],
            hard_fail_on=['low']  # case insensitive
        )
        expected = {
            'soft_fail': False,
            'soft_fail_checks': [],
            'soft_fail_threshold': None,
            'hard_fail_checks': [],
            'hard_fail_threshold': Severities[BcSeverities.LOW]
        }
        self.assertEqual(RunnerRegistry.get_fail_thresholds(config, report_type=CheckType.TERRAFORM), expected)


if __name__ == '__main__':
    unittest.main()
