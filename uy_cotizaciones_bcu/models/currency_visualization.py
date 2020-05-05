# -*- coding: utf-8 -*-

import time
from openerp.tools import float_round
from openerp.osv import osv, fields

class res_currency_template(osv.osv):

    def _current_pizarra_silent(self, cr, uid, ids, name, arg, context=None):
        return self._get_current_pizarra(cr, uid, ids, raise_on_no_rate=False, context=context)

    def _get_current_pizarra(self, cr, uid, ids, raise_on_no_rate=True, context=None):
            if context is None:
                context = {}
            res = {}

            date = context.get('date') or time.strftime('%Y-%m-%d')
            for id in ids:
                cr.execute('SELECT rate FROM res_currency_rate '
                           'WHERE currency_id = %s '
                             'AND name <= %s '
                           'ORDER BY name desc LIMIT 1',
                           (id, date))
                if cr.rowcount:
                    f_val = cr.fetchone()[0]
                    if f_val == 0.0:
                        res[id] = f_val
                    elif f_val < 1:
                        res[id] = 1/f_val
                    else:
                        res[id] = f_val
                elif not raise_on_no_rate:
                    res[id] = 0
                else:
                    currency = self.browse(cr, uid, id, context=context)
                    raise osv.except_osv(_('Error!'),_("No currency pizarra associated for currency '%s' for the given period" % (currency.name)))
            return res


    _inherit = 'res.currency'
    _columns = {
        'pizarra_silent' : fields.function(_current_pizarra_silent, string='Pizarra', digits=(12,6))
    }

res_currency_template()

class res_currency_rate_template(osv.osv):

    def _current_pizarra(self, cr, uid, ids, name, arg, context=None):
        return self._calculate_pizarra(cr, uid, ids, raise_on_no_rate=False, context=context)

    def _calculate_pizarra(self, cr, uid, ids, raise_on_no_rate=True, context=None):
            if context is None:
                context = {}
            res = {}

            date = context.get('date') or time.strftime('%Y-%m-%d')
            for id in ids:
                cr.execute('SELECT rate FROM res_currency_rate '
                           'WHERE id = %s ',
                           (id,))
                if cr.rowcount:
                    f_val = cr.fetchone()[0]
                    if f_val == 0.0:
                        res[id] = float_round(f_val, precision_digits=3)
                    elif f_val < 1:
                        res[id] = float_round(1/f_val, precision_digits=3)
                    else:
                        res[id] = float_round(f_val, precision_digits=3)
                elif not raise_on_no_rate:
                    res[id] = 0
                else:
                    currency = self.browse(cr, uid, id, context=context)
                    raise osv.except_osv(_('Error!'),_("No currency pizarra associated for currency '%s' for the given period" % (currency.name)))
            return res

    _inherit = 'res.currency.rate'
    _columns = {
        'pizarra' : fields.function(_current_pizarra, string='Pizarra', digits=(12,3)),
    }

    def calculate_pizarra_value(self, cr, uid, ids, rate, context=None):

        result = {
            'pizarra': rate
        }

        if rate == 0.0:
            return {'value' : result}

        if rate < 1:
            result['pizarra'] = 1/rate
            return {'value' : result}

        if rate >= 1:
            return {'value' : result}

res_currency_rate_template()