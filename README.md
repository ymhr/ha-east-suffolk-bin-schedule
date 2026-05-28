# East Suffolk Bins

Home Assistant custom integration that fetches bin collection dates from [East Suffolk Council](https://www.eastsuffolk.gov.uk/bins) and exposes them as sensors.

## Requirements

- Home Assistant 2024.1 or newer
- [HACS](https://hacs.xyz) installed

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Click **Integrations** → **⋮** (top right) → **Custom repositories**
3. Add `https://github.com/ymhr/ha-east-suffolk-bin-schedule` with category **Integration**
4. Search for "East Suffolk Bins" and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/east_suffolk_bins/` folder into your HA `/config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **East Suffolk Bins**
3. Enter your UPRN and click Submit

## Finding your UPRN

The easiest way is [uprn.uk](https://uprn.uk):

1. Go to [uprn.uk](https://uprn.uk)
2. Search by postcode
3. Find your address in the list — the UPRN is shown next to it (e.g. `100062012345`)

## Sensors

| Entity | Description |
|--------|-------------|
| `sensor.bin_collection_data` | State = last fetch date. Attributes include `collections` (full list), `today`, `tomorrow`, `error`. |
| `sensor.bins_due_today` | Labels of bins due today (e.g. "📰 Paper and cardboard"). "None" if no collection. Has `count` and `collections` attributes. |
| `sensor.bins_due_tomorrow` | Same pattern for tomorrow's collections. |

## Automation example

```yaml
alias: Bin Reminder
mode: single
trigger:
  - trigger: time
    at: "07:45:00"
    id: morning
  - trigger: time
    at: "19:00:00"
    id: evening
action:
  - choose:
      - conditions:
          - condition: trigger
            id: morning
          - condition: numeric_state
            entity_id: sensor.bins_due_today
            attribute: count
            above: 0
        sequence:
          - action: notify.mobile_app_your_phone
            data:
              title: "🗑️ Bin day today!"
              message: "{{ states('sensor.bins_due_today') }}"
      - conditions:
          - condition: trigger
            id: evening
          - condition: numeric_state
            entity_id: sensor.bins_due_tomorrow
            attribute: count
            above: 0
        sequence:
          - action: notify.mobile_app_your_phone
            data:
              title: "🗑️ Bins out tomorrow!"
              message: "{{ states('sensor.bins_due_tomorrow') }}"
```

Replace `notify.mobile_app_your_phone` with your own notification service.
