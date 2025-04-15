# VK RSS Feed Generator

Generate RSS feeds from VK account and groups.

## Setup

Get a free VK API key from [VK for Business](https://id.vk.com/about/business/go). Register an app then get the Access tokens > Service token

## Usage

Personal accounts:

```
/account/{username}?apiKey={key}
```

Groups:

```
/group/{groupId}?apiKey={key}
```

## Examples

Example RSS: http://cdn.jimchen.me/vk.com/account/durov.rss

```
https://vk-rss.vercel.app/group/mariakhoreva?apiKey=???
https://vk-rss.vercel.app/group/shcherbakova_anna?apiKey=???
https://vk-rss.vercel.app/account/tutberidze.eteri?apiKey=???

```
