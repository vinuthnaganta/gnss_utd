# GNSS-BodyShadow: Can a Phone Feel You Walk By?

## Overview
This project investigates device-free human body sensing. If a phone lies on the ground and a person walks past it, can we see that person in the phone's raw GNSS data, and how does the effect depend on distance and on satellite location?

## Team Members
Vinuthna Ganta, Rishindrasaireddy Vemireddy

## Current Status

* **Phase:** Week 5 - Event Aligned Plots

* **Last Updated:** 2026-11-20

* **Active Milestone:** Uploading all files, parsing data in batches, creating plots.

## Session Protocol
* For each session, take a site photo documenting the setup and weather.
* Place phone in same general area with top of phone pointing to North and flat elevation (+/- 1 degree).
* All other items not used in experiment placed at least 15 meters away.
* Distance walked under conditions: Start and stop position is a total of 6 meters, with phone at center (3 meter point)
* Recorder steps at least 3 meters away from phone once starting.
* Once log has been started, wait 30 seconds before walker walks and 30 seconds after to then stop the log.

## Repository Structure
* `0_papers/` - Literature PDF files and `papers.csv`
* `1_raw_data/` - Read-only raw GNSS logs, videos, and event logs per session
* `2_labels/` - Cleaned versioned labels derived from event logs
* `3_code/` - Python parsers, analysis scripts, requirements, and `run_all.sh`
* `4_slides/` - Weekly presentation decks
* `5_report/` - Final report drafts
