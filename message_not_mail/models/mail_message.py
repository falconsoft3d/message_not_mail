
# coding: utf-8
from odoo import api, fields, models
from datetime import datetime, date, time, timedelta
import calendar


class EmailMailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        # coming from mail.js that does not have pid in its values
        if self.env.context.get('default_starred'):
            self = self.with_context({'default_starred_partner_ids': [(4, self.env.user.partner_id.id)]})
        if 'email_from' not in values:  # needed to compute reply_to
            values['email_from'] = self._get_default_from()
        if not values.get('message_id'):
            values['message_id'] = self._get_message_id(values)
        if 'reply_to' not in values:
            values['reply_to'] = self._get_reply_to(values)
        if 'record_name' not in values and 'default_record_name' not in self.env.context:
            values['record_name'] = self._get_record_name(values)

        context = dict(self.env.context)
        context.update({'message_create_from_mail_mail': True})
        message = super(EmailMailMessage, self.with_context(context)).create(values)
        message._invalidate_documents()
        return message

class EmailMailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    
    @api.multi
    def _message_auto_subscribe_notify(self, partner_ids):
        """ Notify newly subscribed followers of the last posted message.
            :param partner_ids : the list of partner to add as needaction partner of the last message
                                    (This excludes the current partner)
        """
        if not partner_ids:
            return

        if self.env.context.get('mail_auto_subscribe_no_notify'):
            return

        # send the email only to the current record and not all the ids matching active_domain !
        # by default, send_mail for mass_mail use the active_domain instead of active_ids.
        if 'active_domain' in self.env.context:
            ctx = dict(self.env.context)
            ctx.pop('active_domain')
            self = self.with_context(ctx)
       
        # Agregada condicion
        if not self._name in ['account.invoice','sale.order']:
            for record in self:
                record.message_post_with_view(
                    'mail.message_user_assigned',
                    composition_mode='mass_mail',
                    partner_ids=[(4, pid) for pid in partner_ids],
                    auto_delete=True,
                    auto_delete_message=True,
                    parent_id=False, # override accidental context defaults
                    subtype_id=self.env.ref('mail.mt_note').id)
