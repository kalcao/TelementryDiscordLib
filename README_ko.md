# TelementryDiscordLib

[![GitHub stars](https://img.shields.io/github/stars/kalcao/TelementryDiscordLib?style=social)](https://github.com/kalcao/TelementryDiscordLib)
[![GitHub license](https://img.shields.io/github/license/kalcao/TelementryDiscordLib)](https://github.com/kalcao/TelementryDiscordLib)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)

[![English](https://img.shields.io/badge/English-%EB%B3%B4%EA%B8%B0-brightgreen)](README.md)

**TelementryDiscordLib**는 Discord에 **텔레메트리 데이터**를 전송해 플래그(감지)를 피하는 계정 자동화 모듈입니다.

기능: 상태 업데이트, 프로필 편집(휴머나이징), 길드 가입, 멤버 파싱(이름, bio, pfp, activities 등).

> **경고**: 해당 레포는 오직 교육/테스트 및 연구 목적입니다. 전혀 어떠한 스팸을 조장할 의도는 없습니다.

> 설마 오픈소스를 그대로 갖다파는 친구는 없길 바랍니다.

## 위험한 행동

| 행동                | 안전 |
|---------------------|------|
| **상태 업데이트**   | ✅ |
| **프로필 편집**     | ✅ |
| **길드 가입**       | ✅ |
| **멤버 스크랩**     | ✅ |
| **친구 추가**       | ✅ |

## 사용법

```python
from lib.client import DiscordClient

async def main():
    client = DiscordClient("your_token")
    await client.init()

    # 상태 변경
    await client.actions.appearance.change_presence(
        status="dnd", # online/dnd/offline
        activities=[{"type": 0, "name": "Python"}]
    )

    # 프로필 변경
    await client.actions.appearance.change_profile(
        global_name="NewName",
        bio="Bio here"
    )

    # 길드
    await client.actions.guild.join("invite_code")
    members = await client.actions.guild.scrape("guild_id", "channel_id")

    await client.close()

asyncio.run(main())
```

## 업데이트 기록
<details>
<summary>눌러서 펼치기</summary>


<details>
<summary>2025-11-03</summary>
    
```diff
+ 내장솔버 추가
+ actions.relationship.add() 가 플래그되어 토큰 비활성화시키는 문제 해결.
- RazorCap은 플래그되어 deprecated하였습니다.

todo: 솔버 해결. 토큰 100개가 캡챠걸리면 브라우저 100개가 소환되는거
```

</details>

<details>
<summary>2025-11-01</summary>

```diff
+ TelementryDiscordLib 릴리즈
```

</details>

</details>


## 기여

**Fork → Branch → PR**.

디스코드: `@inxtagram`

## 라이선스

[MIT](LICENSE)

## 참고

https://luna.gitlab.io/discord-unofficial-docs/

https://github.com/Merubokkusu/Discord-S.C.U.M

http://discord.food/

https://github.com/RazorCap/RazorCap
