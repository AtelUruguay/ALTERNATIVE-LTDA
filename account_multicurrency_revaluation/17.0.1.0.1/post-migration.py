from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
@openupgrade.logging(args_details=True)
def migrate(env, version):
    """
    The objective of this is delete the original view form the module how bring the functionality
    adding in the previous commit
    """
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            'account_multicurrency_revaluation.view_move_form',
            'account_multicurrency_revaluation.view_account_move_filter',
            'account_multicurrency_revaluation.view_account_form_inherit',
            'account_multicurrency_revaluation.view_account_config_settings',
            'account_multicurrency_revaluation.currency_urealized_report_launcher_wizard',
            'account_multicurrency_revaluation.view_account_currency_revaluation_wizard',
        ],
        delete_childs=True
    )
    env['ir.ui.view'].search([('arch_db', 'like', 'revaluation_to_reverse')]).unlink()
