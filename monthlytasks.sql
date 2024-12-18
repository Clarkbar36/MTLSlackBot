SELECT *
FROM MonthlySchedule
Where MonthNum = strftime('%m', 'now');