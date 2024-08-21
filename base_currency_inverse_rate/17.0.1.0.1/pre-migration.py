from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """
    The objective of this is delete the original view form the module how bring the functionality
    adding in the previous commit
    """
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            'base_currency_inverse_rate.view_currency_rate_tree',
            'base_currency_inverse_rate.view_currency_rate_form',
        ],
        delete_childs=True
    )
