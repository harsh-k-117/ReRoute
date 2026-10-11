# Micro scenario arithmetic

Times are minutes after midnight; 08:00 is 480. The travel matrix uses the location order
`DEPOT, A, B, C, E, F`.

- **V1, load 5 / capacity 5:** Depot→A takes 10 minutes, so D1 arrives at 490 and waits
  10 minutes for its 500 opening. Service ends at 505. A→B takes 5, so D2 arrives at 510,
  starts immediately and ends at 515. Loads after delivery are 2 then 0.
- **V2, load 6 / capacity 6:** Depot→C takes 20, so D3 arrives at 500 and ends at 505.
  C→E takes 5, so D4 arrives at 510 and ends at 515. E→C takes 5, so D5 arrives at
  520 (not 525), starts at 520 and ends at 525. Loads after service are 4, 2, 0.
- **V3, load 6 / capacity 6:** Depot→F takes 30, so D6 arrives at 510 and ends at 515.
  D7 is at the same location and arrives at 515, ending at 520. F→E takes 5, so D8
  arrives at 525 and waits 5 minutes until 530; it ends at 535. Loads are 4, 2, 0.

The sample route intentionally makes V1's capacity binding and demonstrates waiting at D1
and D8. D2's 510 opening is tight to its computed arrival.
