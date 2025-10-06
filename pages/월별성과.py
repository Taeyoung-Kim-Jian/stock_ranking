WITH daily_measure AS (
    SELECT 
        b.종목코드,
        COALESCE(p.종목명, '') AS 종목명,
        b.b가격,
        b.b날짜,
        p.날짜::date AS 측정일,
        p.종가 AS 측정일종가,
        (
            SELECT p_today.종가
            FROM prices p_today
            WHERE p_today.종목코드 = b.종목코드
            ORDER BY ABS(p_today.날짜 - CURRENT_DATE)
            LIMIT 1
        ) AS 현재가,
        ROUND(((p.종가 - b.b가격) / b.b가격 * 100)::numeric, 2) AS 측정일대비수익률,
        (
            SELECT MAX(p2.종가)
            FROM prices p2
            WHERE p2.종목코드 = b.종목코드
              AND p2.날짜 >= p.날짜
        ) AS 이후최고가,
        (
            SELECT MIN(p3.종가)
            FROM prices p3
            WHERE p3.종목코드 = b.종목코드
              AND p3.날짜 >= p.날짜
        ) AS 이후최저가,
        DATE_TRUNC('month', p.날짜)::date AS 월구분
    FROM bt_points b
    JOIN prices p 
        ON b.종목코드 = p.종목코드
        AND p.날짜 BETWEEN '2025-01-28' AND CURRENT_DATE
        AND p.종가 BETWEEN b.b가격 * 0.95 AND b.b가격 * 1.05
)
SELECT to_jsonb(t) AS result
FROM (
    SELECT DISTINCT ON (종목코드, 월구분)
        종목코드,
        종목명,
        b가격,
        b날짜::date AS b날짜,
        측정일,
        측정일종가,
        현재가,
        ROUND(((현재가 - b가격) / b가격 * 100)::numeric, 2) AS 현재가대비수익률,
        이후최고가,
        이후최저가,
        ROUND(((이후최고가 - b가격) / b가격 * 100)::numeric, 2) AS 최고수익률,
        ROUND(((이후최저가 - b가격) / b가격 * 100)::numeric, 2) AS 최저수익률,
        월구분
    FROM daily_measure
    ORDER BY 종목코드, 월구분, 측정일
) t;
