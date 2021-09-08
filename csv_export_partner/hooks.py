def set_default_export_reference(cr, registry):
    partner_obj = registry["res.partner"]
    partner_ids = partner_obj.search(cr, 1, [("export_reference", "=", False)])
    partners = partner_obj.browse(cr, 1, partner_ids)
    for partner in partners:
        partner.export_reference = partner._default_export_reference()
