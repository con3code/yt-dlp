# con3code plugin for upstream yt-dlp

This folder turns the changes made in the con3code/yt-dlp fork into a plugin
that upstream yt-dlp (for example the Homebrew build) can load.

## Use

```shell
yt-dlp --plugin-dirs /path/to/con3code_plugin/plugins URL
```

Pass the `plugins` folder itself, not `yt_dlp_plugins` inside it.
`yt-dlp -v` lists the loaded plugins:

```
[debug] Extractor Plugins: FacebookShareIE, NhkEduSchoolWatchIE, NhkNewsWebIE, RadikoShareIE, ThreadsIE, ThreadsShareIE, con3code (FacebookIE), con3code (InstagramIE), con3code (RadikoIE), con3code (RadikoRadioIE)
```

## What it contains

| Fork change | In the plugin as |
|---|---|
| NHK for School new site (`edu.web.nhk/school/watch/bangumi/`, old `bangumi.cgi`) | new extractor `NhkEduSchoolWatchIE` |
| NHK ONE news articles with video (`news.web.nhk/newsweb/na/...`) | new extractor `NhkNewsWebIE` |
| Instagram: skip photos in posts that mix photos and videos; `img_index=` picks one item | override of `InstagramIE` |
| Threads posts (`threads.com/@user/post/...`) and share links (`threads.com/share/...`) | new extractors `ThreadsIE`, `ThreadsShareIE` |
| Facebook reels: caption/date, and a sign-in error (`--cookies`) for the signed-out page; share links (`facebook.com/share/r/...`, `/share/v/...`) | `FacebookIE` override, new extractor `FacebookShareIE` |
| radiko premium (area-free) login, `--cookies` and `--username/--password` | overrides of `RadikoIE` and `RadikoRadioIE` |
| radiko share links (`radiko.jp/share/?sid=&t=`) | new extractor `RadikoShareIE`, hands the URL to `RadikoIE` |

Share links are a separate extractor because upstream builds use lazy
extractors, where an override cannot change which URLs an extractor matches.

## Regenerate after changing the fork

The fork's `yt_dlp/extractor/radiko.py`, `nhk.py`, `instagram.py`, `threads.py` and `facebook.py` are the only source.
Do not edit the files under `plugins/` by hand.

```shell
python con3code_plugin/generate.py          # rewrite the plugin files
python con3code_plugin/generate.py --check  # exit 1 if they are out of date
```

## Compatibility

- `--plugin-dirs` exists since yt-dlp 2024.10.22. Older versions stop with
  `error: no such option: --plugin-dirs` (exit code 2).
- The plugin code is copied from a fork based on yt-dlp 2026.10.26 and is
  tested with that version. On older versions parts of it fail
  (e.g. 2024.10.22: NHK fails with a `urljoin()` error).
- With the plugin, overridden extractor names get `+con3code`
  (`Radiko+con3code`, `Instagram+con3code`); the extractor keys stay the same.
