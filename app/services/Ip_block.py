import datetime


class LoginAttemptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_ip(self, ip: str):
        result = await self.session.execute(select(LoginAttempt).where(LoginAttempt.ip == ip))
        return result.scalar_one_or_none()

    async def add_attempt(self, ip: str, success: bool):
        row = await self.get_by_ip(ip)

        now = datetime.utcnow()

        if row:
            if success:
                row.attempts = 0
                row.blocked_until = None
            else:
                row.attempts += 1
                if row.attempts >= 5:
                    row.blocked_until = now + timedelta(minutes=15)
        else:
            row = LoginAttempt(
                ip=ip,
                attempts=0 if success else 1,
                blocked_until=None,
            )
            self.session.add(row)
