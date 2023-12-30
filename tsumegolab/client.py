import asyncio

import websockets.client


async def run_client():
    data = '{"moves":[],"initialStones":[["B","L19"],["B","M19"],["B","O19"],["B","Q19"],["B","S19"],["B","F18"],["B","G18"],["B","L18"],["B","N18"],["B","P18"],["B","R18"],["B","T18"],["B","B17"],["B","C17"],["B","D17"],["B","E17"],["B","L17"],["B","M17"],["B","O17"],["B","Q17"],["B","S17"],["B","L16"],["B","N16"],["B","P16"],["B","R16"],["B","T16"],["B","B15"],["B","L15"],["B","M15"],["B","O15"],["B","Q15"],["B","S15"],["B","J14"],["B","K14"],["B","L14"],["B","N14"],["B","P14"],["B","R14"],["B","T14"],["B","F13"],["B","G13"],["B","H13"],["B","J13"],["B","K13"],["B","M13"],["B","O13"],["B","Q13"],["B","S13"],["B","F12"],["B","G12"],["B","J12"],["B","L12"],["B","N12"],["B","P12"],["B","R12"],["B","T12"],["B","A11"],["B","B11"],["B","C11"],["B","D11"],["B","E11"],["B","F11"],["B","H11"],["B","K11"],["B","M11"],["B","O11"],["B","Q11"],["B","S11"],["B","A10"],["B","C10"],["B","E10"],["B","G10"],["B","J10"],["B","L10"],["B","N10"],["B","P10"],["B","R10"],["B","T10"],["B","B9"],["B","D9"],["B","F9"],["B","H9"],["B","K9"],["B","M9"],["B","O9"],["B","Q9"],["B","S9"],["B","A8"],["B","C8"],["B","E8"],["B","G8"],["B","J8"],["B","L8"],["B","N8"],["B","P8"],["B","R8"],["B","T8"],["B","B7"],["B","D7"],["B","F7"],["B","H7"],["B","K7"],["B","M7"],["B","O7"],["B","Q7"],["B","S7"],["B","A6"],["B","C6"],["B","E6"],["B","G6"],["B","J6"],["B","L6"],["B","N6"],["B","P6"],["B","R6"],["B","T6"],["B","B5"],["B","D5"],["B","F5"],["B","H5"],["B","K5"],["B","M5"],["B","O5"],["B","Q5"],["B","S5"],["B","A4"],["B","C4"],["B","E4"],["B","F4"],["B","G4"],["B","H4"],["B","J4"],["B","K4"],["B","L4"],["B","M4"],["B","N4"],["B","O4"],["B","P4"],["B","Q4"],["B","R4"],["B","S4"],["B","T4"],["B","B3"],["B","D3"],["B","F3"],["B","A2"],["B","C2"],["B","E2"],["B","F2"],["B","L2"],["B","M2"],["B","N2"],["B","O2"],["B","P2"],["B","Q2"],["B","B1"],["B","D1"],["B","F1"],["B","O1"],["B","Q1"],["W","B19"],["W","F19"],["W","A18"],["W","B18"],["W","C18"],["W","D18"],["W","G3"],["W","H3"],["W","J3"],["W","K3"],["W","L3"],["W","M3"],["W","N3"],["W","O3"],["W","P3"],["W","Q3"],["W","R3"],["W","S3"],["W","T3"],["W","G2"],["W","R2"],["W","T2"],["W","G1"],["W","K1"],["W","L1"],["W","M1"],["W","R1"],["W","S1"]],"initialPlayer":"B","rules":"japanese","boardXSize":19,"boardYSize":19,"maxVisits":250,"includeOwnership":true}\n'

    async with websockets.client.connect("ws://localhost:15555") as connection:
        await connection.send(data)
        response = await connection.recv()
        print(response)


asyncio.run(run_client())