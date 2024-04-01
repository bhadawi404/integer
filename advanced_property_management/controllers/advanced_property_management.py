# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import werkzeug.utils
from odoo import fields, http
from odoo.http import request


class PropertyController(http.Controller):
    """A controller class that shows the related functions to the property"""

    @http.route('/property', auth='user', website=True)
    def property(self):
        """ Returns the property_view for the route """
        return request.render('advanced_property_management.property_custom', {
            'property_ids': request.env['property.property'].sudo().search([])
        })

    @http.route('/property/<int:property_id>', auth='user', website=True)
    def property_item(self, property_id):
        """ Shows each corresponding properties view in property_view_item """
        api_key = request.env['ir.config_parameter'].sudo().get_param('web_google_maps.api_key')
        property_ids = request.env['property.property'].sudo().search([('id','=', property_id)]).sale_rent
        if property_ids == 'for_auction':
            """Returns properties in three different states"""
            auction_ids = request.env['property.auction'].sudo().search([
                ('state', 'not in', ('draft','canceled')),('property_id', '=', property_id)
            ])
            result = []
            for auction_id in auction_ids:
                participants = sorted(auction_id.participant_ids,key=lambda x: x.bid_amount, reverse=True)
                result.append({
                    'id': auction_id.id,
                    'name': auction_id.property_id.name,
                    'code': auction_id.auction_seq,
                    'image': auction_id.property_id.image,
                    'start': auction_id.start_time,
                    'start_price': auction_id.bid_start_price,
                    'last': participants[0].bid_amount if participants else 0,
                    'end': auction_id.end_time,
                    'winner': auction_id.auction_winner_id.name,
                    'final_rate': auction_id.final_price,
                    'total_participant': len(auction_id.participant_ids.ids),
                    'state': auction_id.state
                })

            value = {
                'property_id': request.env['property.property'].sudo().browse(property_id),
                'auction': result
            }
            return request.render('advanced_property_management.property_detail_view_auction',value)
        if property_ids != 'for_auction':
            return request.render('advanced_property_management.property_detail_view',
                                {
                                    'property_id': request.env[
                                        'property.property'].sudo().browse(
                                        property_id),
                                })

    @http.route('/map/<latitude>/<longitude>', type='http', auth='user')
    def redirect_map(self, latitude, longitude):
        """ Returns the Google map location for the corresponding latitude
        and longitude """
        return werkzeug.utils.redirect(
            "https://www.google.com/maps/@%s,%s,115m/data=!3m1!1e3" % (
                latitude, longitude))
    

    @http.route('/property/auction/', type='http',
                auth='user', website=True)
    def auction_bid_submit(self,**kw):
        """Return success when auction is submitted"""
        auction_id = request.env['property.auction'].sudo().browse(int(kw.get('id')))
        vals = {
            'auction_id': auction_id.id,
            'partner_id': request.env.user.partner_id.id,
            'bid_time': fields.Datetime.now(),
            'bid_amount': float(kw.get('bid_amount'))
        }
        request.env['property.auction.line'].sudo().create(vals)
        return http.request.render('advanced_property_management.success_bid')
