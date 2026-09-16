{
    'name': "Credit Note Return Control",
    'summary': "Require a validated return receipt before posting goods-return credit notes",
    'description': """
Credit Note Return Control
==========================

Blocks the confirmation of customer credit notes issued for a goods return when
there is no evidence that the goods came back into the warehouse.

Every customer credit note must state a reason. When the reason is *Goods
Return*, the credit note must reference a receipt that is validated (Done),
belongs to the same customer, and is not already backing another posted credit
note.

Users in the *Credit Note Return Control Exception* group may bypass the control
by filling in a justification, which is logged in the credit note chatter.

Implemented entirely by inheritance of ``account.move``,
``account.move.reversal`` and ``stock.picking``: no standard model, view or flow
is modified.
""",
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': "Quanam",
    'website': "https://www.quanam.com",
    'license': 'LGPL-3',
    'depends': [
        'account',
        'stock',
    ],
    'data': [
        'security/credit_note_return_control_security.xml',
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'wizard/account_move_reversal_views.xml',
    ],
    'installable': True,
}
