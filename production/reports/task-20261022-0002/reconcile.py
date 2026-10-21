#!/usr/bin/env python3
"""Recompute the report from the adjacent sanitized, frozen API evidence."""
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parent
D = Decimal
GIB = D(1024 ** 3)
LOCAL = timezone(timedelta(hours=8))


def total(rows, field):
    return sum((D(row[field]) for row in rows), D(0))


def utc(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def main():
    data = json.loads((HERE / 'inputs.json').read_text())
    month = data['month_billing_items']
    assert all(row['currency'] == 'CNY' for row in month)
    assert len(month) == 19
    assert len({tuple(sorted(row.items())) for row in month}) == len(month)
    for row in month:
        assert abs(D(row['usage']) * D(row['price']) - D(row['gross'])) < D('0.0000001')
    gross = total(month, 'gross')
    net = total(month, 'net')
    overview = data['overview_oss']
    settlement = data['settlement']
    assert gross == D(overview['PretaxGrossAmount']) == D(settlement['PretaxGrossAmount'])
    assert net == gross
    payable = D(overview['PretaxAmount'])
    assert payable == D(settlement['PretaxAmount'])
    rounding = gross - payable
    assert rounding == D(overview['RoundDownDiscount'])
    assert sum((total(rows, 'net') for rows in data['daily_billing_items'].values()), D(0)) == net
    assert data['other_metering']['network_out_bytes'] == 0
    assert data['other_metering']['storage_byte_hours'] == 0
    assert all(row['region'] == '中国香港' for row in month if D(row['net']))
    assert all(not item.get('next_cursor_present', False) for item in data['lineage'])

    by_item = defaultdict(lambda: {'gross': D(0), 'net': D(0), 'usage': D(0)})
    for row in month:
        item = by_item[row['item_code']]
        for key in item:
            item[key] += D(row[key])
    rate = next(D(row['price']) for row in month if row['item_code'] == 'NetworkOut' and D(row['price']))
    storage_hour_rate = next(D(row['price']) for row in month if row['item_code'] == 'Storage' and D(row['price']))

    hourly = data['hourly_metering']
    keys = [(row['Bucket'], row['Region'], row['StorageType'], row['StartTime']) for row in hourly]
    assert len(set(keys)) == len(keys) == 48
    end = datetime.fromisoformat(data['bill_window']['end_local']).replace(tzinfo=LOCAL)
    billed_hours = [row for row in hourly if utc(row['EndTime']) <= end]
    assert len(billed_hours) == 47
    for first, second in zip(billed_hours, billed_hours[1:]):
        assert first['EndTime'] == second['StartTime']
    metered_bytes = sum(int(row['NetworkOut']) for row in billed_hours)
    metered_gib = D(metered_bytes) / GIB
    billed_gib = by_item['NetworkOut']['usage']
    # Billing Usage is rounded to six decimals per hour; byte metering is exact.
    usage_difference = metered_gib - billed_gib
    assert abs(usage_difference) < D(len(billed_hours)) / D(10 ** 6)
    by_end = {int(utc(row['EndTime']).timestamp() * 1000): int(row['NetworkOut']) for row in hourly}
    assert len(data['cloudmonitor']['points']) == 48
    assert all(by_end[point['timestamp']] == point['bytes'] for point in data['cloudmonitor']['points'])
    top = sorted(billed_hours, key=lambda row: int(row['NetworkOut']), reverse=True)
    extra_bytes = sum(int(row['NetworkOut']) for row in hourly if row not in billed_hours)

    storage_gib = D(data['bucket']['storage_bytes']) / GIB
    # The actual hourly tariff is the source of truth; the monthly column is a
    # 720-hour illustration, not a forecast of the future calendar or tariff.
    storage_month_rate = storage_hour_rate * D(720)
    storage_lower = max(storage_gib - D(5), D(0)) * storage_month_rate
    storage_upper = storage_gib * storage_month_rate
    catalog_gib = D(data['catalog']['bytes']) / GIB
    full_pass = catalog_gib * rate
    film_sizes = [D(row['bytes']) for group in data['films'].values() for row in group]
    film_min, film_max = min(film_sizes) / GIB, max(film_sizes) / GIB
    scenarios = []
    for traffic in [0, 1, 5, 20]:
        monthly_traffic_cost = D(traffic) * D(30) * rate
        scenarios.append({'public_download_GiB_per_day': traffic,
                          'daily_min_CNY': monthly_traffic_cost / D(30) + storage_lower / D(30),
                          'daily_max_CNY': monthly_traffic_cost / D(30) + storage_upper / D(30),
                          'month_30d_min_CNY': monthly_traffic_cost + storage_lower,
                          'month_30d_max_CNY': monthly_traffic_cost + storage_upper})
    daily = {}
    for date, rows in data['daily_billing_items'].items():
        daily[date] = {'rows': len(rows), 'net_CNY_before_bill_rounding': total(rows, 'net'),
                       'public_GiB': sum((D(row['usage']) for row in rows if row['item_code'] == 'NetworkOut'), D(0))}
    result = {
        'task': data['task'], 'gross_CNY': gross, 'bill_payable_CNY': payable,
        'bill_rounding_CNY': rounding, 'bill_payment_CNY': D(settlement['PaymentAmount']),
        'bill_outstanding_CNY': D(settlement['OutstandingAmount']), 'bill_status': settlement['Status'],
        'bill_items': dict(by_item), 'public_download_rate_CNY_per_GiB': rate,
        'public_download_share_of_item_net_percent': by_item['NetworkOut']['net'] / net * 100,
        'daily': daily, 'billed_hours': len(billed_hours), 'metered_billed_window_bytes': metered_bytes,
        'metered_billed_window_GiB': metered_gib, 'bill_public_GiB': billed_gib,
        'metering_minus_bill_GiB': usage_difference,
        'post_bill_window_GiB': D(extra_bytes) / GIB,
        'post_bill_window_estimate_CNY': D(extra_bytes) / GIB * rate,
        'top_7_hours_share_of_billed_window_bytes_percent': D(sum(int(row['NetworkOut']) for row in top[:7])) / D(metered_bytes) * 100,
        'top_hours': [{'start_local': utc(row['StartTime']).astimezone(LOCAL).isoformat(),
                       'download_GiB': D(row['NetworkOut']) / GIB} for row in top[:7]],
        'storage_GiB': storage_gib, 'storage_CNY_per_GiB_hour': storage_hour_rate,
        'storage_720h_CNY_per_GiB': storage_month_rate,
        'storage_30d_min_CNY_assuming_current_5GiB_free': storage_lower,
        'storage_30d_max_CNY_without_free': storage_upper,
        'catalog_GiB': catalog_gib, 'one_full_public_catalog_pass_CNY': full_pass,
        'four_catalog_passes_plus_storage_30d_CNY': [full_pass * 4 + storage_lower, full_pass * 4 + storage_upper],
        'publication_archives_GiB': D(data['catalog']['publication_archive_bytes']) / GIB,
        'film_full_fetch_min_CNY': film_min * rate, 'film_full_fetch_max_CNY': film_max * rate,
        'ten_film_fetches_daily_30d_CNY_no_download_free': [film_min * 300 * rate + storage_lower, film_max * 300 * rate + storage_upper],
        'twenty_CNY_per_day_download_GiB': D(20) / rate,
        'traffic_scenarios_no_download_free_no_requests': scenarios,
        'checks': {'monthly_daily_totals_equal': True, 'gross_usage_price_consistent': True,
                   'bill_overview_settlement_equal': True, 'rounding_reconciled': True,
                   'hourly_unique_contiguous': True, 'cloudmonitor_all_points_equal_oms': True,
                   'bucket_attribution_metering_supported': True, 'all_pagination_complete': True}
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n'
    (HERE / 'calculations.json').write_text(encoded)
    print(encoded, end='')


if __name__ == '__main__':
    main()
