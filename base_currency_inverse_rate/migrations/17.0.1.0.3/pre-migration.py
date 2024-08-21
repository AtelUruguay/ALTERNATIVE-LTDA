from openupgradelib import openupgrade
import logging

_logger = logging.getLogger(__name__)

@openupgrade.migrate(use_env=True)
@openupgrade.logging(args_details=True)
def migrate(env, version):
    """
    The objective of this is delete the original view form the module how bring the functionality
    adding in the previous commit
    """
    _logger.info('************ base_currency_inverse_rate MIGRATION')
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            'base_currency_inverse_rate.view_currency_rate_tree',
            'base_currency_inverse_rate.view_currency_rate_form',
        ],
        delete_childs=True
    )
