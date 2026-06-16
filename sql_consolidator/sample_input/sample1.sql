-- Sample SQL File 1: Production Queries

SELECT
    u.id,
    u.username,
    u.email,
    COUNT(o.id) AS total_orders,
    SUM(o.total_amount) AS lifetime_value
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.is_active = 1
GROUP BY u.id, u.username, u.email
HAVING COUNT(o.id) > 0
ORDER BY lifetime_value DESC;

-- DUPLICATE (different formatting - should be removed)
select u.id, u.username, u.email,
count(o.id) as total_orders, sum(o.total_amount) as lifetime_value
from users u left join orders o on u.id = o.user_id
where u.is_active = 1
group by u.id, u.username, u.email
having count(o.id) > 0 order by lifetime_value desc;

INSERT INTO audit_log (user_id, action, timestamp)
VALUES (@user_id, 'LOGIN', GETDATE());

UPDATE users
SET last_login = GETDATE(), login_count = login_count + 1
WHERE id = @user_id;

CREATE TABLE IF NOT EXISTS user_sessions (
    session_id  VARCHAR(255) PRIMARY KEY,
    user_id     INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP,
    is_active   BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

WITH monthly_revenue AS (
    SELECT DATE_FORMAT(created_at, '%Y-%m') AS month,
           SUM(amount) AS revenue, COUNT(*) AS order_count
    FROM orders WHERE status = 'completed'
    GROUP BY DATE_FORMAT(created_at, '%Y-%m')
)
SELECT * FROM monthly_revenue ORDER BY revenue DESC;

-- RISKY: DELETE without WHERE
DELETE FROM temp_processing_queue;

DROP TABLE IF EXISTS old_backup_2019;

ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL;
