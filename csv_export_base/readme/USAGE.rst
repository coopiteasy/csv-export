* add a module ``csv_export_<model>``
* add a transient model ``csv.export.<model>`` inheriting from ``csv.export.base`` and
   * implement ``get_domain``, ``get_headers`` and ``get_rows``
   * set ``_connector_model`` (eg. "account.payment")
   * set ``_filename_template`` (eg. "CASH_%Y%m%d_%H%M.csv")
* add a view and menu for that model (examples in module ``account_export_payment``)
* add a boolean field ``exported_to_sftp`` on exported model.
* If needed configure a sftp server in the menu Configuration > SFTP Servers
   * add export line referencing the csv.export.<model> you created.
