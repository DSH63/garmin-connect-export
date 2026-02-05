#!/usr/bin/env python3
"""
Analyze SUP sessions for qualifying 1km segments with high stroke rate.

Criteria:
- Sessions with total_distance > 4.9 km
- Qualifying segment: consecutive laps with cumulative distance >= 1.0 km
  and weighted average stroke rate >= 48 strokes/min
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


# Configuration
DB_PATH = Path(__file__).parent / "sup_analysis.db"
MIN_SESSION_DISTANCE_KM = 4.9
MIN_SEGMENT_DISTANCE_KM = 1.0
MIN_STROKE_RATE = 48.0


@dataclass
class QualifyingSegment:
    """A consecutive sequence of laps meeting the criteria."""
    start_lap: int
    end_lap: int
    distance_km: float
    weighted_stroke_rate: float
    total_strokes: int
    total_time_sec: float
    avg_distance_per_stroke: float  # meters per stroke


@dataclass
class SessionResult:
    """Analysis result for a single session."""
    session_id: int
    date: str
    total_distance_km: float
    qualifying_segment: Optional[QualifyingSegment]


def find_qualifying_segment(laps: list[tuple]) -> Optional[QualifyingSegment]:
    """
    Find the first consecutive sequence of laps where:
    - Cumulative distance >= MIN_SEGMENT_DISTANCE_KM
    - Weighted avg stroke rate >= MIN_STROKE_RATE

    Laps format: (lap_number, distance, time, strokes)
    Returns the first qualifying segment found, or None.
    """
    n = len(laps)
    min_distance_m = MIN_SEGMENT_DISTANCE_KM * 1000

    for start in range(n):
        cumulative_distance = 0.0
        cumulative_time = 0.0
        cumulative_strokes = 0

        for end in range(start, n):
            lap_num, distance, time, strokes = laps[end]

            # Skip laps with missing data
            if distance is None or time is None or strokes is None:
                break
            if time <= 0:
                break

            cumulative_distance += distance
            cumulative_time += time
            cumulative_strokes += strokes

            # Check if we've reached minimum distance
            if cumulative_distance >= min_distance_m:
                weighted_stroke_rate = (cumulative_strokes / cumulative_time) * 60

                if weighted_stroke_rate >= MIN_STROKE_RATE:
                    dps = cumulative_distance / cumulative_strokes
                    return QualifyingSegment(
                        start_lap=laps[start][0],
                        end_lap=lap_num,
                        distance_km=cumulative_distance / 1000,
                        weighted_stroke_rate=weighted_stroke_rate,
                        total_strokes=cumulative_strokes,
                        total_time_sec=cumulative_time,
                        avg_distance_per_stroke=dps
                    )
                # Found distance but rate too low - try next start position
                break

    return None


def analyze_sessions(db_path: Path) -> list[SessionResult]:
    """Analyze all qualifying sessions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get sessions > 4.9km
    min_distance_m = MIN_SESSION_DISTANCE_KM * 1000
    cursor.execute("""
        SELECT id, start_time, total_distance
        FROM sessions
        WHERE total_distance > ?
        ORDER BY start_time
    """, (min_distance_m,))

    sessions = cursor.fetchall()
    results = []

    for session_id, start_time, total_distance in sessions:
        # Get laps for this session
        cursor.execute("""
            SELECT lap_number, distance, time, strokes
            FROM laps
            WHERE session_id = ?
            ORDER BY lap_number
        """, (session_id,))

        laps = cursor.fetchall()
        qualifying_segment = find_qualifying_segment(laps)

        # Format date from datetime string
        date = start_time.split()[0] if start_time else "Unknown"

        results.append(SessionResult(
            session_id=session_id,
            date=date,
            total_distance_km=total_distance / 1000,
            qualifying_segment=qualifying_segment
        ))

    conn.close()
    return results


def print_results(results: list[SessionResult]) -> None:
    """Print analysis results."""
    total_sessions = len(results)
    qualifying_sessions = [r for r in results if r.qualifying_segment is not None]
    qualifying_count = len(qualifying_sessions)

    print("=" * 70)
    print("SUP SESSION ANALYSIS: High Stroke Rate Segments")
    print("=" * 70)
    print(f"\nCriteria:")
    print(f"  - Session distance: > {MIN_SESSION_DISTANCE_KM} km")
    print(f"  - Segment distance: >= {MIN_SEGMENT_DISTANCE_KM} km (consecutive laps)")
    print(f"  - Stroke rate:      >= {MIN_STROKE_RATE} strokes/min (weighted avg)")
    print()

    print("-" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"  Total sessions > {MIN_SESSION_DISTANCE_KM}km:     {total_sessions}")
    print(f"  Sessions with qualifying segment: {qualifying_count}")
    if total_sessions > 0:
        percentage = (qualifying_count / total_sessions) * 100
        print(f"  Percentage:                       {percentage:.1f}%")

    # Calculate segment percentages for qualifying sessions
    segment_percentages = []
    for r in qualifying_sessions:
        seg_pct = (r.qualifying_segment.distance_km / r.total_distance_km) * 100
        segment_percentages.append(seg_pct)

    if segment_percentages:
        avg_pct = sum(segment_percentages) / len(segment_percentages)
        min_pct = min(segment_percentages)
        max_pct = max(segment_percentages)
        print()
        print(f"  Segment % of session (qualifying):")
        print(f"    Average: {avg_pct:.1f}%  |  Min: {min_pct:.1f}%  |  Max: {max_pct:.1f}%")

    # Calculate DPS stats for qualifying sessions
    dps_values = [r.qualifying_segment.avg_distance_per_stroke for r in qualifying_sessions]
    if dps_values:
        avg_dps = sum(dps_values) / len(dps_values)
        min_dps = min(dps_values)
        max_dps = max(dps_values)
        print()
        print(f"  Distance per stroke (qualifying):")
        print(f"    Average: {avg_dps:.2f} m  |  Min: {min_dps:.2f} m  |  Max: {max_dps:.2f} m")
    print()

    if qualifying_sessions:
        print("-" * 70)
        print("QUALIFYING SESSIONS")
        print("-" * 70)
        print()

        for result in qualifying_sessions:
            seg = result.qualifying_segment
            seg_pct = (seg.distance_km / result.total_distance_km) * 100
            print(f"  {result.date}  |  {result.total_distance_km:.2f} km total")
            print(f"    Segment: Laps {seg.start_lap}-{seg.end_lap}  |  "
                  f"{seg_pct:.1f}% of session")
            print(f"    Distance: {seg.distance_km:.2f} km  |  "
                  f"Stroke Rate: {seg.weighted_stroke_rate:.1f} spm  |  "
                  f"DPS: {seg.avg_distance_per_stroke:.2f} m  |  "
                  f"Time: {seg.total_time_sec/60:.1f} min")
            print()

    # Also show non-qualifying sessions for reference
    non_qualifying = [r for r in results if r.qualifying_segment is None]
    if non_qualifying:
        print("-" * 70)
        print("NON-QUALIFYING SESSIONS (no 1km segment >= 48 spm)")
        print("-" * 70)
        for result in non_qualifying:
            print(f"  {result.date}  |  {result.total_distance_km:.2f} km")

    print()
    print("=" * 70)


def main():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return 1

    results = analyze_sessions(DB_PATH)
    print_results(results)
    return 0


if __name__ == "__main__":
    exit(main())
