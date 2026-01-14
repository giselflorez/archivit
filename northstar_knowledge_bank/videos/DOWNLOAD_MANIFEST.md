# NORTHSTAR MASTERS VIDEO DOWNLOAD MANIFEST
## Tracking Video Downloads for Cognitive Mapping

**Created:** January 12, 2026
**Last Updated:** January 12, 2026 04:20
**Location:** `/northstar_knowledge_bank/videos/downloads/`

---

## COMPLETED DOWNLOADS

### Session 2 (2026-01-12 - Agent Init Session)
| File | Master | Size | Source |
|------|--------|------|--------|
| Rand_Mike_Wallace_Interview_1959.webm | Ayn Rand | 97MB | archive.org/details/youtube-lHl2PqwRcY0 |
| Tesla_Mysterious_Mr_1982.mp4 | Nikola Tesla | 79MB | archive.org/details/11-2-the-mysterious-mr.-tesla-1982 |
| Bowie_Cracked_Actor_BBC_1975.mpg | David Bowie | 1.3GB | archive.org/details/BBC_A_Film_By_Bowie_Cracked_Actor_1975 |

### Session 1 (2026-01-12 - Video Archive)
| File | Master | Duration | Size | Source |
|------|--------|----------|------|--------|
| Jung_BBC_Face_to_Face_1959.webm | Carl Jung | 38 min | 91MB | archive.org/details/youtube-2AMu-G51yTY |
| Tesla_Master_of_Lightning_2000.mp4 | Nikola Tesla | 85 min | 504MB | archive.org/details/TeslaMasterOfLightning |
| Coltrane_World_According_To_1990.mp4 | John Coltrane | 59 min | 347MB | archive.org/details/the-world-according-to-john-coltrane-1990 |
| Jobs_iPhone_Introduction_2007.mp4 | Steve Jobs | 80 min | 492MB | archive.org/details/original-iphone-keynote |
| Fuller_World_of_1971.mp4 | Buckminster Fuller | 85 min | 239MB | archive.org/details/World-of-B-Fuller-1971 |
| Fuller_Part01.mp4 | Buckminster Fuller | ~45 min | 51MB | archive.org/details/buckminsterfullereverythingiknow01 |

**TOTAL DOWNLOADED:** ~3.2GB (9 videos)

---

## DOWNLOAD QUEUE (To Be Downloaded)

### High Priority
| Video | Master | Size | Archive.org ID |
|-------|--------|------|----------------|
| Fuller Everything I Know (All 12 Parts) | Fuller | ~26GB | buckminsterfullereverythingiknow01-12 |
| Jobs Stanford Commencement 2005 | Jobs | ~200MB | stevejobsarchive.com |
| Bowie Cracked Actor 1975 | Bowie | ~500MB | Various |

### Medium Priority
| Video | Master | Source |
|-------|--------|--------|
| Prince Larry King 1999 | Prince | CNN Archive |
| Jung Richard Evans 1957 | Jung | Bitchute |
| Jobs Lost Interview 1995 | Jobs | Netflix/Streaming |

---

## TOTAL STORAGE ESTIMATES

| Category | Size |
|----------|------|
| Completed Downloads | ~942MB |
| In Progress | ~780MB |
| Fuller Full Series | ~26GB |
| **Total Projected** | **~28GB** |

---

## TRANSCRIPTION STATUS

**Requirement:** ffmpeg installation needed for automated transcription
```bash
# Install ffmpeg, then use Whisper:
brew install ffmpeg
whisper "video.mp4" --model base --language English
```

### Key Quotes Files Created (Manual Transcription)

| File | Status | Location |
|------|--------|----------|
| Jung_BBC_Face_to_Face_1959_KEY_QUOTES.md | COMPLETE | /transcripts/ |
| Coltrane_Key_Quotes.md | COMPLETE | /transcripts/ |
| Jobs_Key_Quotes.md | COMPLETE | /transcripts/ |
| Fuller_Key_Quotes.md | COMPLETE | /transcripts/ |

**Contents:** Verified quotes with sources, cognitive mapping notes, expression analysis

### Full Transcription Queue (Pending ffmpeg)

1. **Jung BBC Face to Face (1959)** - 38 min
2. **Jobs iPhone Introduction (2007)** - 80 min
3. **Fuller World of (1971)** - 85 min
4. **Coltrane World According To (1990)** - 59 min
5. **Fuller Everything I Know (1975)** - 42 HOURS (official transcripts at bfi.org)

---

## FILE NAMING CONVENTION

```
[LastName]_[Title]_[Year].[ext]
Examples:
- Jung_BBC_Face_to_Face_1959.webm
- Fuller_Everything_I_Know_Part01.mp4
- Jobs_iPhone_Introduction_2007.mp4
```

---

## DOWNLOAD SCRIPTS

### Fuller Full Download
Location: `/northstar_knowledge_bank/videos/download_fuller.sh`
Usage: `./download_fuller.sh`
Note: Downloads all 12 parts (~26GB total)

---

## PROVENANCE TRACKING

All videos are:
- From Archive.org (public domain / educational use)
- Cataloged in `docs/MASTERS_VIDEO_ARCHIVE.md`
- For NORTHSTAR cognitive mapping purposes

---

*This manifest is auto-updated with each download session.*
