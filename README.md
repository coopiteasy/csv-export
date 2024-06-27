
<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->
[![Pre-commit Status](https://github.com/coopiteasy/csv-connector/actions/workflows/pre-commit.yml/badge.svg?branch=12.0)](https://github.com/coopiteasy/csv-connector/actions/workflows/pre-commit.yml?query=branch%3A12.0)
[![Build Status](https://github.com/coopiteasy/csv-connector/actions/workflows/test.yml/badge.svg?branch=12.0)](https://github.com/coopiteasy/csv-connector/actions/workflows/test.yml?query=branch%3A12.0)
[![codecov](https://codecov.io/gh/coopiteasy/csv-connector/branch/12.0/graph/badge.svg)](https://codecov.io/gh/coopiteasy/csv-connector)
<!-- /!\ Non OCA Context : Set here the badge of your translation instance. -->

<!-- /!\ do not modify above this line -->

# CSV export and upload tools

This repository contains tools to export data as CSV and upload it to a server.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[csv_export_base](csv_export_base/) | 12.0.1.1.0 |  | Base to create module to export csv files.
[csv_export_partner](csv_export_partner/) | 12.0.1.1.0 |  | Export your partners as CSV flat files
[csv_export_payment](csv_export_payment/) | 12.0.1.1.0 |  | Export your payments as CSV flat files
[sftp_backend](sftp_backend/) | 12.0.1.0.0 |  | SFTP backend utils.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Coop IT Easy SC
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
