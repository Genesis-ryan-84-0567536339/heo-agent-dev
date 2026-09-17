#!/usr/bin/env node
/**
 * AGY Zalo Co-Pilot Bridge
 * Standalone integration connecting Zalo to Google Antigravity (AGY) Engine
 * With Group Context Awareness, Member Resolution & Strict Silence Policy
 */

const fs = require("fs");
const path = require("path");
const http = require("http");
const axios = require("axios");
const qrcode = require("qrcode-terminal");
const crypto = require("crypto");
const { Zalo, ThreadType, LoginQRCallbackEventType, Reactions } = require("zca-js");
const { imageSize } = require("image-size");

const BASE_DIR = process.env.BASE_DIR || path.resolve(__dirname, "..");
const DATA_DIR = process.env.DATA_DIR || path.join(BASE_DIR, "data");
const WORKSPACE_DIR = process.env.WORKSPACE_DIR || path.join(BASE_DIR, "workspace");
const LOG_DIR = process.env.LOG_DIR || path.join(BASE_DIR, "logs");
const SCRIPTS_DIR = process.env.SCRIPTS_DIR || path.join(BASE_DIR, "scripts");
const CONFIG_FILE = process.env.CONFIG_FILE || path.join(BASE_DIR, "config", "config.json");
const SESSION_FILE = path.join(DATA_DIR, "zalo_session.json");
const QR_PATH = path.join(WORKSPACE_DIR, "zalo_qr.png");
const AGY_ENGINE_URL = process.env.AGY_ENGINE_URL || "http://127.0.0.1:5066";
const OUTBOUND_PORT = parseInt(process.env.BRIDGE_PORT || "5051", 10);

let config = {};
let BOSS_UID = process.env.BOSS_UID || "";
let BOSS_NAME = process.env.BOSS_NAME || "Sếp";
let BOSS_CALLER_NAME = process.env.BOSS_CALLER_NAME || "Sếp";
let BOT_NAME = "Bé Heo";

function loadConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      config = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8"));
      BOSS_UID = process.env.BOSS_UID || config.boss_uid || "";
      BOSS_NAME = config.boss_name || "Sếp";
      BOSS_CALLER_NAME = config.boss_caller_name || "Sếp";
      BOT_NAME = config.bot_name || "Bé Heo";
    }
  } catch (e) {
    console.error("Warning: Could not read config file", e.message);
  }
  return config;
}

loadConfig();

const QR_ONLY = process.argv.includes("--qr-only");

function verifyPin(inputPin) {
  if (!inputPin) return false;
  const trimmed = String(inputPin).trim();
  const cfg = loadConfig();
  const currentHash = cfg.pin_hash || "";
  const currentPlain = cfg.pin_code ? String(cfg.pin_code).trim() : "";

  if (!currentHash && !currentPlain) {
    return false;
  }

  const inputHash = crypto.createHash("sha256").update(trimmed).digest("hex");
  if (currentHash && inputHash.toLowerCase() === currentHash.toLowerCase()) {
    return true;
  }
  if (currentPlain && (trimmed === currentPlain || inputHash.toLowerCase() === crypto.createHash("sha256").update(currentPlain).digest("hex").toLowerCase())) {
    return true;
  }
  return false;
}

function hasPinConfigured() {
  const cfg = loadConfig();
  return Boolean(cfg.pin_hash || cfg.pin_code);
}

async function checkIsFriend(api, userId) {
  if (!userId) return false;
  try {
    const res = await api.getUserInfo(userId);
    const profile = res?.changed_profiles?.[userId] || res?.unchanged_profiles?.[userId];
    if (profile && (profile.isFr === 1 || profile.isFr === true)) {
      return true;
    }
  } catch (e) {}
  try {
    const friends = await api.getAllFriends();
    if (Array.isArray(friends) && friends.some(f => String(f.userId || f.id) === String(userId))) {
      return true;
    }
  } catch (e) {}
  return false;
}

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(WORKSPACE_DIR)) fs.mkdirSync(WORKSPACE_DIR, { recursive: true });
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

// Bộ nhớ đệm chống trùng tin nhắn (Message Deduplication Cache)
const processedMsgIds = new Set();
// Cache thông tin thành viên & tên nhóm
const userCache = new Map();
const groupCache = new Map();

function log(msg) {
  const ts = new Date().toISOString().replace(/T/, " ").replace(/\..+/, "");
  console.log(`[${ts}] [AGY-Zalo] ${msg}`);
}

async function getUserDisplayName(api, userId) {
  if (!userId) return "Thành viên";
  if (BOSS_UID && String(userId) === BOSS_UID) return BOSS_NAME;
  if (userCache.has(userId)) return userCache.get(userId);
  try {
    const res = await api.getUserInfo(userId);
    const profile = res?.changed_profiles?.[userId] || res?.unchanged_profiles?.[userId];
    if (profile && (profile.zaloName || profile.displayName)) {
      const name = profile.zaloName || profile.displayName;
      userCache.set(userId, name);
      return name;
    }
  } catch (e) {}
  return `Thành viên (${userId})`;
}

async function getGroupDetails(api, groupId) {
  if (!groupId) return { name: "Nhóm Zalo" };
  if (groupCache.has(groupId)) return groupCache.get(groupId);
  try {
    const res = await api.getGroupInfo(groupId);
    const info = res?.gridInfoMap?.[groupId];
    if (info) {
      const details = { name: info.name || "Nhóm Zalo", creatorId: info.creatorId };
      groupCache.set(groupId, details);
      return details;
    }
  } catch (e) {}
  return { name: "Nhóm Zalo" };
}

const GROUPS_FILE = path.join(DATA_DIR, "active_groups.json");

function appendGroupHistory(groupId, item) {
  try {
    const historyFile = path.join(DATA_DIR, `group_${groupId}.jsonl`);
    fs.appendFileSync(historyFile, JSON.stringify(item) + "\n", "utf-8");
  } catch (e) {}
}

function findMessageSnippet(groupId, targetMsgId) {
  if (!targetMsgId) return "";
  try {
    const historyFile = path.join(DATA_DIR, `group_${groupId}.jsonl`);
    if (!fs.existsSync(historyFile)) return "";
    const lines = fs.readFileSync(historyFile, "utf-8").trim().split("\n");
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const item = JSON.parse(lines[i]);
        if (item.msgId && String(item.msgId) === String(targetMsgId)) {
          return item.text ? item.text.substring(0, 60).replace(/\n/g, " ") : "";
        }
      } catch (e) {}
    }
  } catch (err) {}
  return "";
}

function parseReactionDetails(rIcon, rType) {
  const mapByIcon = {
    "/-heart": { icon: "❤️", name: "Thả tim", sentiment: "positive", meaning: "Rất thích, hài lòng, đồng tình cao" },
    "/-strong": { icon: "👍", name: "Like", sentiment: "positive", meaning: "Đồng ý, duyệt, tán thành, đã xác nhận" },
    ":>": { icon: "😂", name: "Haha", sentiment: "positive", meaning: "Hài hước, vui vẻ, thích thú" },
    ":')": { icon: "🤣", name: "Cười nghiêng ngả", sentiment: "positive", meaning: "Rất buồn cười, sảng khoái" },
    ":o": { icon: "😮", name: "Wow", sentiment: "neutral", meaning: "Bất ngờ, ngạc nhiên, ấn tượng" },
    ":-((": { icon: "😢", name: "Buồn", sentiment: "negative", meaning: "Buồn, tiếc nuối, chưa hài lòng, có khúc mắc hoặc gặp khó khăn" },
    ":-h": { icon: "😡", name: "Phẫn nộ", sentiment: "negative", meaning: "BÁO ĐỘNG ĐỎ: Bực tức, phản đối gay gắt, phẫn nộ, cảnh báo nghiêm trọng" },
    "/-weak": { icon: "👎", name: "Dislike", sentiment: "negative", meaning: "BÁO ĐỘNG ĐỎ: Không thích, chê, phản đối" },
    "/-break": { icon: "💔", name: "Tan vỡ", sentiment: "negative", meaning: "Thất vọng, hụt hẫng" },
    "/-rose": { icon: "🌹", name: "Tặng hoa", sentiment: "positive", meaning: "Biết ơn, khen ngợi, cảm kích" },
    "_()_": { icon: "🙏", name: "Biết ơn/Chắp tay", sentiment: "positive", meaning: "Cảm ơn chân thành, nhờ vả lịch thiệp" },
    ":-*": { icon: "😘", name: "Hôn/Yêu", sentiment: "positive", meaning: "Yêu mến, thân thiết" },
    "/-clap": { icon: "👏", name: "Vỗ tay", sentiment: "positive", meaning: "Tán thưởng, chúc mừng" },
    ":handclap": { icon: "👏", name: "Vỗ tay", sentiment: "positive", meaning: "Tán thưởng, chúc mừng" }
  };

  const mapByType = {
    5: { icon: "❤️", name: "Thả tim", sentiment: "positive", meaning: "Rất thích, hài lòng, đồng tình cao" },
    3: { icon: "👍", name: "Like", sentiment: "positive", meaning: "Đồng ý, duyệt, tán thành, đã xác nhận" },
    0: { icon: "😂", name: "Haha", sentiment: "positive", meaning: "Hài hước, vui vẻ, thích thú" },
    7: { icon: "🤣", name: "Cười nghiêng ngả", sentiment: "positive", meaning: "Rất buồn cười, sảng khoái" },
    32: { icon: "😮", name: "Wow", sentiment: "neutral", meaning: "Bất ngờ, ngạc nhiên, ấn tượng" },
    2: { icon: "😢", name: "Buồn", sentiment: "negative", meaning: "Buồn, tiếc nuối, chưa hài lòng, có khúc mắc hoặc gặp khó khăn" },
    20: { icon: "😡", name: "Phẫn nộ", sentiment: "negative", meaning: "BÁO ĐỘNG ĐỎ: Bực tức, phản đối gay gắt, phẫn nộ, cảnh báo nghiêm trọng" },
    14: { icon: "👎", name: "Dislike", sentiment: "negative", meaning: "BÁO ĐỘNG ĐỎ: Không thích, chê, phản đối" },
    4: { icon: "👎", name: "Dislike", sentiment: "negative", meaning: "BÁO ĐỘNG ĐỎ: Không thích, chê, phản đối" },
    120: { icon: "🌹", name: "Tặng hoa", sentiment: "positive", meaning: "Biết ơn, khen ngợi, cảm kích" },
    65: { icon: "💔", name: "Tan vỡ", sentiment: "negative", meaning: "Thất vọng, hụt hẫng" },
    46: { icon: "👏", name: "Vỗ tay", sentiment: "positive", meaning: "Tán thưởng, chúc mừng" }
  };

  if (rIcon && mapByIcon[rIcon]) return mapByIcon[rIcon];
  if (rType !== undefined && mapByType[rType]) return mapByType[rType];
  return { icon: "✨", name: "Tương tác", sentiment: "neutral", meaning: "Tương tác cảm xúc" };
}

async function syncAllActiveGroups(api) {
  try {
    const allGroupsRes = await api.getAllGroups();
    const groupIds = Object.keys(allGroupsRes?.gridVerMap || {});
    const groupsData = {};

    for (const gid of groupIds) {
      try {
        const info = await api.getGroupInfo(gid);
        const g = info?.gridInfoMap?.[gid];
        if (!g) continue;

        const memberIds = (g.memberIds && g.memberIds.length > 0) 
          ? g.memberIds 
          : (g.memVerList ? g.memVerList.map(m => m.split("_")[0]) : []);
        let memberProfiles = [];
        try {
          const memInfo = await api.getGroupMembersInfo(memberIds);
          const profs = memInfo?.profiles || {};
          memberProfiles = memberIds.map(mid => {
            const p = profs[mid];
            let name = p?.zaloName || p?.displayName || mid;
            if (String(mid) === BOSS_UID) name = "${BOSS_NAME}";
            return {
              id: String(mid),
              name,
              isBoss: String(mid) === BOSS_UID
            };
          });
        } catch (memErr) {
          memberProfiles = memberIds.map(mid => ({
            id: String(mid),
            name: String(mid) === BOSS_UID ? "${BOSS_NAME}" : `Thành viên (${mid})`,
            isBoss: String(mid) === BOSS_UID
          }));
        }

        groupsData[gid] = {
          groupId: gid,
          groupName: g.name || "Nhóm Zalo",
          creatorId: g.creatorId,
          totalMember: g.totalMember || memberIds.length,
          members: memberProfiles,
          lastUpdated: new Date().toISOString()
        };
        groupCache.set(gid, { name: g.name || "Nhóm Zalo", creatorId: g.creatorId });
        // Tự động kéo lịch sử gần nhất từ máy chủ Zalo để đảm bảo không sót tin nhắn
        backfillGroupChatHistory(api, gid).catch(() => {});
      } catch (e) {
        log(`⚠️ Lỗi lấy info group ${gid}: ${e.message}`);
      }
    }

    fs.writeFileSync(GROUPS_FILE, JSON.stringify(groupsData, null, 2), "utf-8");
    log(`📋 Đã đồng bộ ${Object.keys(groupsData).length} nhóm Zalo vào ${GROUPS_FILE}`);
    return groupsData;
  } catch (err) {
    log(`⚠️ Lỗi syncAllActiveGroups: ${err.message}`);
    return {};
  }
}

async function backfillGroupChatHistory(api, groupId) {
  try {
    const historyRes = await api.getGroupChatHistory(String(groupId), 50);
    const msgs = historyRes?.groupMsgs || [];
    if (!msgs || msgs.length === 0) return;

    const historyFile = path.join(DATA_DIR, `group_${groupId}.jsonl`);
    const existingMsgIds = new Set();
    if (fs.existsSync(historyFile)) {
      const lines = fs.readFileSync(historyFile, "utf-8").trim().split("\n");
      for (const line of lines) {
        try {
          const item = JSON.parse(line);
          if (item.msgId) existingMsgIds.add(String(item.msgId));
        } catch (e) {}
      }
    }

    let addedCount = 0;
    msgs.sort((a, b) => (Number(a.data?.ts) || 0) - (Number(b.data?.ts) || 0));

    for (const m of msgs) {
      const mId = String(m.data?.msgId || m.data?.id || "");
      if (mId && existingMsgIds.has(mId)) continue;

      const uid = String(m.data?.uidFrom || "");
      const dName = m.data?.dName || await getUserDisplayName(api, uid);
      let content = "";
      if (typeof m.data?.content === "string") {
        content = m.data.content.trim();
      } else if (m.data?.content && typeof m.data.content === "object") {
        const c = m.data.content;
        content = [c.title || c.description, c.href || c.url].filter(Boolean).join(" ");
      }

      if (!content && !m.data?.quote) continue;

      const ts = m.data?.ts ? new Date(Number(m.data.ts)).toISOString() : new Date().toISOString();
      const record = {
        time: ts,
        msgId: mId,
        senderUid: uid,
        senderName: dName,
        text: content
      };
      appendGroupHistory(groupId, record);
      if (mId) existingMsgIds.add(mId);
      addedCount++;
    }
    if (addedCount > 0) {
      log(`📥 [Đồng bộ lịch sử Zalo]: Đã nạp bổ sung ${addedCount} tin nhắn trước đó vào nhóm ${groupId}`);
    }
  } catch (err) {
    // Bỏ qua lỗi nếu API chưa sẵn sàng
  }
}

async function imageMetadataGetter(filePath) {
  try {
    const buf = await fs.promises.readFile(filePath);
    const dims = imageSize(buf);
    return {
      width: dims.width || 800,
      height: dims.height || 600,
      size: buf.length
    };
  } catch (err) {
    try {
      const stat = fs.statSync(filePath);
      return { width: 800, height: 600, size: stat.size };
    } catch {
      return { width: 800, height: 600, size: 1024 };
    }
  }
}

async function initZaloClient() {
  const zalo = new Zalo({
    selfListen: true,
    imageMetadataGetter
  });
  let api = null;

  if (fs.existsSync(SESSION_FILE)) {
    try {
      log("🔑 Nạp phiên đăng nhập Zalo lưu trữ...");
      const sessionData = JSON.parse(fs.readFileSync(SESSION_FILE, "utf-8"));
      api = await zalo.login(sessionData);
      log("✅ Đăng nhập Zalo thành công bằng phiên cookie!");
      return api;
    } catch (err) {
      log(`⚠️ Phiên cũ không hợp lệ: ${err.message}. Chuyển sang mã QR...`);
    }
  }

  while (true) {
    try {
      log("⚡ Đang tạo mã QR đăng nhập Zalo...");
      api = await zalo.loginQR({ qrPath: QR_PATH }, async (evt) => {
        switch (evt.type) {
          case LoginQRCallbackEventType.QRCodeGenerated: {
            log("📱 ĐÃ TẠO MÃ QR ĐĂNG NHẬP!");
            let qrPayload = "";

            // 1. Thử giải mã trực tiếp từ ảnh QR chính thức của Zalo bằng jsQR & pngjs
            try {
              if (evt.data && evt.data.image) {
                const { PNG } = require("pngjs");
                const jsQR = require("jsqr");
                const imgBuffer = Buffer.from(evt.data.image, "base64");
                const png = PNG.sync.read(imgBuffer);
                const qrResult = jsQR(new Uint8ClampedArray(png.data.buffer), png.width, png.height);
                if (qrResult && qrResult.data) {
                  qrPayload = qrResult.data;
                }
              }
            } catch (_) {}

            // 2. Dự phòng: Sử dụng evt.data.token theo đúng giao thức Zalo login
            if (!qrPayload && evt.data && evt.data.token) {
              qrPayload = evt.data.token.startsWith("http")
                ? evt.data.token
                : `http://zaloapp.com/qr/l?tk=${evt.data.token}`;
            }

            // 3. Dự phòng cuối cùng: evt.data.code
            if (!qrPayload && evt.data && evt.data.code) {
              qrPayload = evt.data.code.startsWith("http")
                ? evt.data.code
                : (evt.data.code.startsWith("zaloqr:")
                    ? `http://zaloapp.com/qr/l?tk=${evt.data.code}`
                    : evt.data.code);
            }

            if (qrPayload) {
              console.log("\n" + "═".repeat(60));
              console.log("👉 BẮT BUỘC: Mở app ZALO trên điện thoại di động");
              console.log("👉 Bấm biểu tượng [ -|- ] (Quét mã QR) ở góc trên bên phải Zalo");
              console.log("   (LƯU Ý: Không dùng camera thường của máy để quét!)");
              console.log("👉 Quét mã QR dưới đây, rồi bấm 'ĐĂNG NHẬP' trên điện thoại");
              console.log("═".repeat(60) + "\n");
              qrcode.generate(qrPayload, { small: true });
            }

            if (evt.actions && evt.actions.saveToFile) {
              await evt.actions.saveToFile(QR_PATH);
            } else if (evt.data && evt.data.image) {
              fs.writeFileSync(QR_PATH, Buffer.from(evt.data.image, "base64"));
            }

            try {
              const dataQrPath = path.join(DATA_DIR, "zalo_qr.png");
              if (fs.existsSync(QR_PATH)) {
                fs.copyFileSync(QR_PATH, dataQrPath);
              }
              const qrInfoPath = path.join(DATA_DIR, "zalo_qr_info.json");
              fs.writeFileSync(qrInfoPath, JSON.stringify({
                created_at: Date.now(),
                expires_in: 100,
                scanned: false,
                declined: false,
                user_name: ""
              }), "utf-8");
            } catch (_) {}

            console.log(`\n🖼️ Ảnh QR gốc đã được lưu tại: ${QR_PATH}`);
            console.log("   (Sếp cũng có thể mở trực tiếp file ảnh này để quét nếu terminal bị vỡ dòng!)\n");
            break;
          }
          case LoginQRCallbackEventType.QRCodeScanned: {
            const userName = evt.data?.display_name || evt.data?.name || "";
            log(`👁️ Sếp${userName ? " (" + userName + ")" : ""} đã quét mã QR! Vui lòng bấm 'ĐĂNG NHẬP' trên điện thoại để hoàn tất...`);
            try {
              const qrInfoPath = path.join(DATA_DIR, "zalo_qr_info.json");
              let currentInfo = {};
              if (fs.existsSync(qrInfoPath)) {
                try { currentInfo = JSON.parse(fs.readFileSync(qrInfoPath, "utf-8")); } catch (_) {}
              }
              fs.writeFileSync(qrInfoPath, JSON.stringify({
                ...currentInfo,
                scanned: true,
                scanned_at: Date.now(),
                user_name: userName,
                avatar: evt.data?.avatar || ""
              }), "utf-8");
            } catch (_) {}
            break;
          }
          case LoginQRCallbackEventType.GotLoginInfo: {
            log("🎉 NHẬN THÔNG TIN XÁC THỰC ZALO THÀNH CÔNG!");
            fs.writeFileSync(SESSION_FILE, JSON.stringify(evt.data, null, 2), "utf-8");
            log(`Đã lưu phiên làm việc vào: ${SESSION_FILE}`);
            try {
              if (fs.existsSync(QR_PATH)) fs.unlinkSync(QR_PATH);
              const dataQrPath = path.join(DATA_DIR, "zalo_qr.png");
              if (fs.existsSync(dataQrPath)) fs.unlinkSync(dataQrPath);
              const qrInfoPath = path.join(DATA_DIR, "zalo_qr_info.json");
              if (fs.existsSync(qrInfoPath)) fs.unlinkSync(qrInfoPath);
            } catch (_) {}
            if (QR_ONLY) {
              log("✅ [QR Setup] Đã xác thực Zalo thành công! Thoát chế độ thiết lập QR.");
              setTimeout(() => process.exit(0), 1000);
            }
            break;
          }
          case LoginQRCallbackEventType.QRCodeExpired:
            log("⏳ Mã QR hết hạn trên Zalo. Đang tự động làm mới mã QR mới...");
            try {
              const qrInfoPath = path.join(DATA_DIR, "zalo_qr_info.json");
              if (fs.existsSync(qrInfoPath)) fs.unlinkSync(qrInfoPath);
            } catch (_) {}
            break;
          case LoginQRCallbackEventType.QRCodeDeclined:
            log("❌ Từ chối đăng nhập trên điện thoại. Đang tạo mã QR mới...");
            try {
              const qrInfoPath = path.join(DATA_DIR, "zalo_qr_info.json");
              fs.writeFileSync(qrInfoPath, JSON.stringify({
                scanned: false,
                declined: true,
                created_at: Date.now()
              }), "utf-8");
            } catch (_) {}
            break;
        }
      });

      if (api) return api;
    } catch (qrErr) {
      log(`⚠️ Quá trình quét mã QR (${qrErr.message}). Đang tự động tạo lại mã QR mới sau 2s...`);
      try {
        if (fs.existsSync(QR_PATH)) fs.unlinkSync(QR_PATH);
        const dataQrPath = path.join(DATA_DIR, "zalo_qr.png");
        if (fs.existsSync(dataQrPath)) fs.unlinkSync(dataQrPath);
        const qrInfoPath = path.join(DATA_DIR, "zalo_qr_info.json");
        if (fs.existsSync(qrInfoPath)) fs.unlinkSync(qrInfoPath);
      } catch (_) {}
      await new Promise(r => setTimeout(r, 2000));
    }
  }
}

function getRandomInterimMessage(isGroup, isBoss, senderName, prompt) {
  const isDoc = /bài|thi|tiểu luận|báo cáo|kế hoạch|tài liệu|soạn|viết|docx|doc/i.test(prompt || "");
  const isSheet = /tính|sheet|excel|bảng|số liệu|xlsx/i.test(prompt || "");

  if (isGroup) {
    if (isDoc) {
      const options = [
        "Dạ đợi em một chút nhen, em đang soạn xong gửi vào nhóm liền ạ! 📄✨",
        "Dạ em đang căn chỉnh file nốt, sắp xong rồi em gửi liền nha! 👌",
        "Dạ em đang hoàn thiện tài liệu, xong cái là em gửi ngay ạ! 🥰",
        "Dạ đợi em xíu xiu, em soạn xong gửi vào nhóm ngay đây ạ! ✍️",
        "Dạ em đang làm nốt phần này, xong em gửi file liền nha! ✨"
      ];
      return options[Math.floor(Math.random() * options.length)];
    } else if (isSheet) {
      const options = [
        "Dạ em đang chạy bảng tính và ráp số liệu, xong em gửi vào nhóm liền ạ! 📊",
        "Dạ đợi em một xíu nhen, em tính toán xong gửi file ngay ạ! 👌",
        "Dạ em đang đối soát bảng số liệu nốt, sắp có file gửi nhóm rồi ạ! 📈",
        "Dạ đợi em xíu, em xuất bảng tính gửi vào nhóm ngay đây ạ! ✨"
      ];
      return options[Math.floor(Math.random() * options.length)];
    } else {
      const options = [
        "Dạ đợi em một xíu nhen, em gửi kết quả ngay ạ! ✨",
        "Dạ em đang xử lý, sắp xong rồi nha! 👌",
        "Dạ đợi em một chút xíu, xong em gửi liền ạ! 🥰",
        "Dạ em đang làm nốt, có kết quả em gửi ngay ạ! ⏳"
      ];
      return options[Math.floor(Math.random() * options.length)];
    }
  } else {
    if (isDoc) {
      const options = [
        "Dạ Sếp đợi em một chút, em soạn thảo xong gửi Sếp liền ạ! 📄✨",
        "Dạ em đang rà soát nốt tài liệu, xong em gửi Sếp ngay nha! 👌",
        "Dạ phần này em đang hoàn thiện, sắp xong rồi Sếp nha! 🥰"
      ];
      return options[Math.floor(Math.random() * options.length)];
    } else if (isSheet) {
      const options = [
        "Dạ Sếp đợi em xíu, em đang chạy bảng tính gửi Sếp liền ạ! 📊",
        "Dạ em đang ráp số liệu cho chuẩn, xong em gửi file Sếp ngay nha! 📈",
        "Dạ em đang kiểm tra lại bảng số liệu, xong em gửi Sếp liền ạ! 👌"
      ];
      return options[Math.floor(Math.random() * options.length)];
    } else {
      const options = [
        "Dạ Sếp đợi em một xíu nhen, xong em gửi Sếp liền ạ! ✨",
        "Dạ em đang xử lý, sắp xong rồi Sếp nha! 👌",
        "Dạ em đang làm nốt, em báo cáo Sếp ngay đây ạ! 🚀"
      ];
      return options[Math.floor(Math.random() * options.length)];
    }
  }
}

function getRandomSecondInterimMessage(isGroup, isBoss) {
  if (isGroup) {
    const options = [
      "Dạ phần này hơi dài một xíu, em vẫn đang làm nốt đây ạ, sắp có rồi nha! 🏃‍♀️💨",
      "Dạ mọi người đợi em thêm tí xíu nhen, em đang rà soát lại cho chuẩn chỉ ạ! ✨",
      "Dạ sắp xong rồi nhen, em gửi vào nhóm ngay đây ạ! 🥰"
    ];
    return options[Math.floor(Math.random() * options.length)];
  } else {
    const options = [
      "Dạ Sếp đợi em thêm tí xíu nhen, phần này hơi chi tiết nên em đang làm nốt ạ! 🏃‍♀️💨",
      "Dạ em đang rà soát khâu cuối, sắp xong rồi Sếp nha! ✨"
    ];
    return options[Math.floor(Math.random() * options.length)];
  }
}

function splitText(text, maxLength = 1800) {
  if (!text || text.length <= maxLength) return [text || ""];
  const chunks = [];
  let remaining = text;
  while (remaining.length > maxLength) {
    let splitIdx = remaining.lastIndexOf("\n", maxLength);
    if (splitIdx === -1 || splitIdx < maxLength / 2) {
      splitIdx = remaining.lastIndexOf(". ", maxLength);
      if (splitIdx !== -1) splitIdx += 1;
    }
    if (splitIdx === -1 || splitIdx < maxLength / 2) {
      splitIdx = maxLength;
    }
    chunks.push(remaining.substring(0, splitIdx).trim());
    remaining = remaining.substring(splitIdx).trim();
  }
  if (remaining.length > 0) {
    chunks.push(remaining);
  }
  return chunks;
}

const recentSentMessages = [];

function trackSentMessage(res, threadId, threadType, msgText) {
  try {
    const mId = res?.data?.msgId || res?.message?.msgId || res?.msgId || "";
    const cId = res?.data?.cliMsgId || res?.message?.cliMsgId || res?.cliMsgId || "";
    if (mId || cId) {
      recentSentMessages.push({
        msgId: String(mId),
        cliMsgId: String(cId || mId),
        threadId: String(threadId),
        threadType,
        text: String(msgText || ""),
        time: Date.now()
      });
      if (recentSentMessages.length > 60) recentSentMessages.shift();
    }
  } catch (e) {}
}

async function sendSafeMessage(api, payload, threadId, threadType) {
  const msg = typeof payload === "string" ? payload : (payload.msg || "");
  const attachments = (payload && payload.attachments) || [];
  const quote = payload && payload.quote;

  let finalRes = null;
  // Xử lý gửi kèm file đính kèm
  if (attachments.length > 0) {
    if (msg.length > 1800) {
      const chunks = splitText(msg, 1800);
      finalRes = await api.sendMessage({ msg: chunks[0], attachments, quote }, threadId, threadType);
      trackSentMessage(finalRes, threadId, threadType, chunks[0]);
      for (let i = 1; i < chunks.length; i++) {
        const subRes = await api.sendMessage({ msg: chunks[i] }, threadId, threadType);
        trackSentMessage(subRes, threadId, threadType, chunks[i]);
      }
      return finalRes;
    } else {
      finalRes = await api.sendMessage({ msg, attachments, quote }, threadId, threadType);
      trackSentMessage(finalRes, threadId, threadType, msg);
      return finalRes;
    }
  }

  // Xử lý chỉ gửi văn bản
  if (msg.length > 1800) {
    const chunks = splitText(msg, 1800);
    let firstRes = null;
    for (let i = 0; i < chunks.length; i++) {
      const p = (i === 0 && quote) ? { msg: chunks[i], quote } : { msg: chunks[i] };
      const res = await api.sendMessage(p, threadId, threadType);
      trackSentMessage(res, threadId, threadType, chunks[i]);
      if (i === 0) firstRes = res;
    }
    return firstRes;
  }

  finalRes = await api.sendMessage(payload, threadId, threadType);
  trackSentMessage(finalRes, threadId, threadType, msg);
  return finalRes;
}

async function startBridge() {
  let api = null;
  try {
    api = await initZaloClient();
  } catch (err) {
    log(`❌ Lỗi khởi động Zalo Client: ${err.message}`);
    process.exit(1);
  }

  let ownId = null;
  try {
    ownId = api.getOwnId();
    log(`🤖 AGY Zalo Co-Pilot trực chiến! (Tài khoản ID: ${ownId})`);
    try {
      fs.writeFileSync(path.join(DATA_DIR, "zalo_profile.json"), JSON.stringify({ ownId, updatedAt: new Date().toISOString() }, null, 2), "utf-8");
    } catch (_) {}
  } catch (e) {
    log(`🤖 AGY Zalo Co-Pilot đã kết nối thành công!`);
  }

  // Khởi chạy Outbound HTTP Server (Port 5051)
  try {
    const server = http.createServer(async (req, res) => {
      if (req.method === "GET" && req.url === "/api/info") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ ok: true, connected: true, ownId: ownId || "" }));
        return;
      }

      if (req.method === "GET" && req.url === "/api/groups") {
        try {
          if (fs.existsSync(GROUPS_FILE)) {
            const content = fs.readFileSync(GROUPS_FILE, "utf-8");
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(content);
            return;
          }
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({}));
        } catch (e) {
          res.writeHead(500, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: e.message }));
        }
        return;
      }

      if (req.method === "POST" && req.url === "/api/send") {
        let body = "";
        req.on("data", chunk => body += chunk);
        req.on("end", async () => {
          try {
            const payload = JSON.parse(body);
            const { threadId, threadType, msg, attachments } = payload;
            await sendSafeMessage(api, { msg, attachments }, String(threadId), threadType !== undefined ? threadType : ThreadType.User);
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true }));
          } catch (err) {
            res.writeHead(500, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: err.message }));
          }
        });
        return;
      }

      if (req.method === "POST" && req.url === "/api/react") {
        let body = "";
        req.on("data", chunk => body += chunk);
        req.on("end", async () => {
          try {
            const payload = JSON.parse(body);
            const { threadId, threadType, msgId, cliMsgId, icon } = payload;
            let iconEnum = Reactions.LIKE;
            const ic = String(icon || "").trim();
            if (ic === "❤️" || ic === "HEART" || ic === "/-heart") iconEnum = Reactions.HEART;
            else if (ic === "👍" || ic === "LIKE" || ic === "/-strong") iconEnum = Reactions.LIKE;
            else if (ic === "😂" || ic === "HAHA" || ic === ":>") iconEnum = Reactions.HAHA;
            else if (ic === "😮" || ic === "WOW" || ic === ":o") iconEnum = Reactions.WOW;
            else if (ic === "😢" || ic === "CRY" || ic === ":-((") iconEnum = Reactions.CRY;
            else if (ic === "😡" || ic === "ANGRY" || ic === ":-h") iconEnum = Reactions.ANGRY;
            else if (ic === "🌹" || ic === "ROSE" || ic === "/-rose") iconEnum = Reactions.ROSE;
            else if (ic === "🙏" || ic === "PRAY" || ic === "_()_") iconEnum = Reactions.PRAY;
            else if (ic === "👏" || ic === "CLAP" || ic === "/-clap") iconEnum = Reactions.HANDCLAP;

            const dest = {
              type: threadType !== undefined ? threadType : ThreadType.User,
              threadId: String(threadId),
              data: {
                msgId: String(msgId),
                cliMsgId: String(cliMsgId || msgId)
              }
            };
            await api.addReaction(iconEnum, dest);
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: true }));
          } catch (err) {
            res.writeHead(500, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: err.message }));
          }
        });
        return;
      }

      if (req.method === "POST" && req.url === "/api/undo") {
        let body = "";
        req.on("data", chunk => body += chunk);
        req.on("end", async () => {
          try {
            const payload = JSON.parse(body);
            const { threadId, threadType } = payload;
            const targetThreadId = String(threadId);
            const tType = threadType !== undefined ? threadType : ThreadType.Group;
            // Tìm tin nhắn gần nhất mà bot đã gửi trong thread này
            const lastMsg = recentSentMessages.slice().reverse().find(m => String(m.threadId) === targetThreadId);
            if (lastMsg && lastMsg.msgId) {
              await api.undo({ msgId: lastMsg.msgId, cliMsgId: lastMsg.cliMsgId || lastMsg.msgId }, targetThreadId, tType);
              const idx = recentSentMessages.indexOf(lastMsg);
              if (idx !== -1) recentSentMessages.splice(idx, 1);
              log(`🗑️ [Undo Message] Đã thu hồi thành công tin nhắn "${lastMsg.text?.substring(0, 40)}..." trong thread ${targetThreadId}`);
              res.writeHead(200, { "Content-Type": "application/json" });
              res.end(JSON.stringify({ ok: true, undoneMsgId: lastMsg.msgId }));
              return;
            }
            res.writeHead(404, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: "Không tìm thấy tin nhắn bot để thu hồi" }));
          } catch (err) {
            log(`⚠️ [Undo Error]: ${err.message}`);
            res.writeHead(500, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ok: false, error: err.message }));
          }
        });
        return;
      }
      res.writeHead(404);
      res.end();
    });
    server.on("error", (err) => {
      if (err.code === "EADDRINUSE") {
        log(`⚠️ Cổng ${OUTBOUND_PORT} đang bận (EADDRINUSE). Chờ giải phóng và khởi động lại sau 2s...`);
        setTimeout(() => process.exit(1), 2000);
      } else {
        log(`⚠️ Lỗi HTTP Server: ${err.message}`);
      }
    });
    server.listen(OUTBOUND_PORT, "127.0.0.1", () => {
      log(`🚀 Zalo Outbound HTTP Server listening on http://127.0.0.1:${OUTBOUND_PORT} (/api/send, /api/react)`);
    });
  } catch (srvErr) {
    log(`⚠️ Không thể mở Outbound Server: ${srvErr.message}`);
  }

  // Tự động đồng bộ các nhóm Zalo ban đầu và định kỳ 3 phút
  syncAllActiveGroups(api).catch(() => {});
  setInterval(() => syncAllActiveGroups(api).catch(() => {}), 180000);

  // Lắng nghe tin nhắn
  api.listener.on("message", async (msg) => {
    try {
      const threadId = msg.threadId;
      const msgType = msg.type;
      const senderUid = msg.data?.uidFrom;
      const msgId = msg.data?.msgId || msg.data?.id;

      // 1. Chống trùng tin nhắn (Deduplication)
      if (msgId) {
        if (processedMsgIds.has(msgId)) {
          return;
        }
        processedMsgIds.add(msgId);
        if (processedMsgIds.size > 200) {
          const first = processedMsgIds.values().next().value;
          processedMsgIds.delete(first);
        }
      }

      let rawContent = "";
      if (typeof msg.data?.content === "string") {
        rawContent = msg.data.content.trim();
      } else if (msg.data?.content && typeof msg.data.content === "object") {
        const c = msg.data.content;
        rawContent = [c.title || c.description, c.href || c.url].filter(Boolean).join(" ");
      }

      // Tự động nhận diện và chuyển hóa tin nhắn thoại (Voice Message Transcription)
      if (rawContent.includes("voice-aac-dl.zdn.vn") || rawContent.match(/^https?:\/\/.*\.aac(\?.*)?$/i)) {
        try {
          const { execSync } = require("child_process");
          const transcribed = execSync(`python3 "${path.join(SCRIPTS_DIR, "transcribe_voice.py")}" "${rawContent}"`, { timeout: 25000, encoding: "utf-8" }).trim();
          if (transcribed) {
            log(`🎙️ [Voice Transcribe] -> ${transcribed.replace(/\n/g, " ")}`);
            if (transcribed.startsWith("[")) {
              rawContent = transcribed;
            } else {
              rawContent = `[Tin nhắn thoại: "${transcribed}"]`;
            }
          }
        } catch (sttErr) {
          log(`⚠️ Không thể transcribe voice message: ${sttErr.message}`);
        }
      }

      log(`📩 Tin nhắn: type=${msgType === ThreadType.Group ? 'Group' : '1-1'}, sender=${senderUid}, isSelf=${msg.isSelf}, thread=${threadId}, text="${rawContent.substring(0, 60)}"`);

      // 2. CHẶN VÒNG LẶP TỰ TRẢ LỜI CHÍNH MÌNH (SELF-REPLY LOOP PREVENTION)
      const isSelfMessage = Boolean(msg.isSelf || (ownId && String(senderUid) === String(ownId)));
      if (isSelfMessage) {
        try {
          const mId = msg.data?.msgId || msg.data?.id || "";
          const cId = msg.data?.cliMsgId || "";
          if (mId) {
            recentSentMessages.push({
              msgId: String(mId),
              cliMsgId: String(cId || mId),
              threadId: String(threadId),
              threadType: msgType,
              text: rawContent,
              time: Date.now()
            });
            if (recentSentMessages.length > 60) recentSentMessages.shift();
          }
        } catch (e) {}
        if (!/^\s*@heo\b/i.test(rawContent)) {
          return;
        }
        rawContent = rawContent.replace(/^\s*@heo\s*/i, "").trim();
      }

      // 3. CHAT 1-1 VỚI SẾP HOẶC XÁC THỰC OWNER BẰNG MÃ PIN
      if (msgType === ThreadType.User) {
        if (!rawContent && !msg.data?.quote) return;

        loadConfig();

        // -------------------------------------------------------------
        // TRƯỜNG HỢP 1: HỆ THỐNG CHƯA GHÉP NỐI OWNER (!BOSS_UID)
        // -------------------------------------------------------------
        if (!BOSS_UID) {
          // 1. Kiểm tra bạn bè: Chỉ người có kết bạn Zalo với Heo mới được ghép nối
          const isFriend = await checkIsFriend(api, senderUid);
          if (!isFriend) {
            log(`🔒 [Pairing Warning] Người dùng UID=${senderUid} chưa kết bạn Zalo với Heo. Yêu cầu kết bạn trước.`);
            await sendSafeMessage(api, {
              msg: `👋 Chào bạn! Bé Heo đang chờ kết nối với Chủ nhân (Owner/Admin).\n\n⚠️ Để nhận quyền Quản trị viên, bạn cần **KẾT BẠN ZALO** với Heo trước nhé!\nSau khi kết bạn thành công, hãy gửi tin nhắn kèm **Mã PIN bảo mật** (đã thiết lập trên Heo Console) để xác thực.`
            }, threadId, ThreadType.User);
            return;
          }

          // 2. Đã là bạn bè. Kiểm tra xem hệ thống đã tạo mã PIN trên Heo Console (HCS) chưa
          if (!hasPinConfigured()) {
            log(`⚠️ [Pairing Notice] UID=${senderUid} là bạn bè nhắn tin nhưng hệ thống chưa tạo mã PIN trên HCS.`);
            await sendSafeMessage(api, {
              msg: `🔐 [XÁC THỰC QUYỀN CHỦ NHÂN - OWNER PAIRING]\n\n👋 Chào bạn! Heo đang sẵn sàng kết nối.\n⚠️ Tuy nhiên, hệ thống hiện tại **chưa có Mã PIN bảo mật**.\n\nVui lòng truy cập **Heo Console (HCS)** tại: http://localhost:5066 để tạo Mã PIN bảo mật trước, sau đó gửi mã PIN vào đây để nhận quyền Owner nhé!`
            }, threadId, ThreadType.User);
            return;
          }

          // 3. Hệ thống đã có mã PIN. Trích xuất mã PIN từ tin nhắn:
          let candidatePin = rawContent.trim();
          const pinRegex = /(?:mã\s*pin|pin)\s*[:=\s]\s*([a-zA-Z0-9_-]+)/i;
          const match = rawContent.match(pinRegex);
          if (match && match[1]) {
            candidatePin = match[1];
          }

          const isPinValid = verifyPin(candidatePin) || verifyPin(rawContent.trim());

          if (isPinValid) {
            const newBossUid = String(senderUid);
            const bossDisplayName = await getUserDisplayName(api, senderUid);
            const newBossName = (bossDisplayName && !bossDisplayName.startsWith("Thành viên")) ? bossDisplayName : "Sếp";
            
            // Đọc lại file cấu hình hiện tại để giữ nguyên các thiết lập khác
            let currentCfg = {};
            try {
              if (fs.existsSync(CONFIG_FILE)) {
                currentCfg = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8"));
              }
            } catch (e) {}

            currentCfg.boss_uid = newBossUid;
            currentCfg.boss_name = newBossName;

            try {
              fs.writeFileSync(CONFIG_FILE, JSON.stringify(currentCfg, null, 2), "utf-8");
              log(`👑 [Owner Paired Success] Đã xác thực thành công Chủ nhân: ${newBossName} (UID: ${newBossUid}) qua mã PIN! Đã lưu vào ${CONFIG_FILE}`);
            } catch (e) {
              log(`⚠️ Lỗi lưu config file: ${e.message}`);
            }

            // Cập nhật bộ nhớ biến runtime
            config = currentCfg;
            BOSS_UID = newBossUid;
            BOSS_NAME = newBossName;

            await sendSafeMessage(api, {
              msg: `🎉 [XÁC THỰC CHỦ NHÂN THÀNH CÔNG!]\n\n👑 Heo xin kính chào Sếp ${BOSS_NAME}!\nHeo đã xác thực Mã PIN thành công và chính thức nhận Sếp là **Chủ nhân (Owner/Admin)** duy nhất của hệ thống.\n\nTừ bây giờ, Sếp có toàn quyền chỉ đạo Heo qua Zalo và quản trị hệ thống trên Heo Console (HCS). Bé Heo luôn sẵn sàng phục vụ Sếp ạ! 🥰✨`
            }, threadId, ThreadType.User);
            return;
          } else {
            const looksLikePin = (rawContent.trim().length <= 20 && /^[a-zA-Z0-9_-]+$/.test(rawContent.trim())) || Boolean(match);
            if (looksLikePin) {
              log(`❌ [Pairing Failed] UID=${senderUid} nhập sai mã PIN: "${rawContent.trim()}"`);
              await sendSafeMessage(api, {
                msg: `❌ [MÃ PIN KHÔNG CHÍNH XÁC]\n\nMã PIN bạn vừa nhập không khớp với mã PIN bảo mật trên Heo Console (HCS).\n\nVui lòng kiểm tra lại trên Heo Console (http://localhost:5066) và gửi lại đúng mã PIN để xác thực quyền Owner nhé!`
              }, threadId, ThreadType.User);
            } else {
              log(`🔐 [Pairing Request] UID=${senderUid} nhắn tin nhưng chưa gửi mã PIN.`);
              await sendSafeMessage(api, {
                msg: `🔐 [XÁC THỰC QUYỀN CHỦ NHÂN - OWNER PAIRING]\n\n👋 Chào bạn! Để kết nối và nhận quyền Quản trị viên (Owner/Admin) của Bé Heo, vui lòng gửi **Mã PIN bảo mật** (đã thiết lập trên Heo Console) vào đây nhé!\n\n👉 Cú pháp: Chỉ cần nhắn trực tiếp mã PIN vào đây (Ví dụ: 123456).`
              }, threadId, ThreadType.User);
            }
            return;
          }
        }

        // -------------------------------------------------------------
        // TRƯỜNG HỢP 2: ĐÃ CÓ BOSS_UID NHƯNG NGƯỜI NHẮN KHÔNG PHẢI SẾP
        // -------------------------------------------------------------
        if (BOSS_UID && String(senderUid) !== BOSS_UID) {
          log(`⚠️ Tin nhắn 1-1 từ tài khoản lạ (UID=${senderUid}): "${rawContent.substring(0, 40)}"`);
          await sendSafeMessage(api, {
            msg: `Dạ Heo chào bạn! Heo là trợ lý AI riêng của Sếp ${BOSS_NAME}. Nếu bạn cần liên hệ hoặc trao đổi công việc, bạn có thể nhắn vào nhóm chung có Sếp và Heo nhé! 🥰`
          }, threadId, ThreadType.User);
          return;
        }

        // -------------------------------------------------------------
        // TRƯỜNG HỢP 3: SẾP CHÍNH THỨC NHẮN TIN (senderUid === BOSS_UID)
        // -------------------------------------------------------------
        let userPrompt = rawContent;
        if (msg.data?.quote && msg.data.quote.msg) {
          userPrompt = `[Trích dẫn tin nhắn: "${msg.data.quote.msg}"]\n\nYêu cầu: ${rawContent || "Hãy xử lý nội dung trên"}`.trim();
        }

        log(`[1-1 ${BOSS_NAME}] "${userPrompt.substring(0, 60)}..."`);
        appendGroupHistory("boss_1on1", {
          time: new Date().toISOString(),
          msgId: String(msgId || ""),
          senderUid: BOSS_UID,
          senderName: BOSS_NAME,
          text: userPrompt
        });
        await api.sendTypingEvent(threadId, ThreadType.User).catch(() => {});

        // 1. Lệnh tra cứu trạng thái mô hình & cấu hình nhanh
        if (/^\/(model|status)\s*$/i.test(userPrompt.trim())) {
          try {
            const stResp = await axios.get(`${AGY_ENGINE_URL}/api/status`, { timeout: 5000 });
            const st = stResp.data;
            const statusMsg = (
              `📊 [BÁO CÁO HẠ TẦNG AI - TRẠNG THÁI MODEL]\n\n` +
              `🔹 Mô hình hiện tại: ${st.active_model}\n` +
              `🔹 Mức suy luận (Effort): ${(st.effort || 'medium').toUpperCase()}\n` +
              `🔹 Chế độ: ${st.is_fallback ? '⚠️ Fallback do quota' : '✅ Bình thường'}\n` +
              `🔹 Web UI Quản trị: http://localhost:5066\n\n` +
              `💡 CÚ PHÁP ĐỔI NHANH:\n` +
              `👉 /model flash (hoặc 3.8 / pro / sonnet / opus)\n` +
              `👉 /effort low | medium | high`
            );
            await sendSafeMessage(api, { msg: statusMsg, quote: msg.data }, threadId, ThreadType.User);
            return;
          } catch (e) {}
        }

        // 2. Lệnh chuyển đổi model nhanh
        const modelMatch = userPrompt.trim().match(/^\/(?:model|use|switch)\s+(.+)$/i) ||
                           userPrompt.trim().match(/^(?:đổi|chuyển)\s+(?:sang\s+)?(?:model|mô hình)\s+(.+)$/i);
        if (modelMatch) {
          const target = modelMatch[1].trim();
          try {
            const swResp = await axios.post(`${AGY_ENGINE_URL}/api/switch_model`, { model: target }, { timeout: 5000 });
            const sw = swResp.data;
            if (sw.ok) {
              await sendSafeMessage(api, {
                msg: `✅ Dạ Sếp, em đã chuyển mô hình hoạt động sang: ${sw.active_model} (Effort: ${(sw.effort || 'medium').toUpperCase()})!`,
                quote: msg.data
              }, threadId, ThreadType.User);
              return;
            }
          } catch (e) {}
        }

        // 3. Lệnh chuyển đổi mức suy luận (Effort)
        const effortMatch = userPrompt.trim().match(/^\/effort\s+(low|medium|high|thấp|vừa|cao)$/i) ||
                            userPrompt.trim().match(/^(?:chỉnh|đổi|tăng|hạ)\s+effort\s+(low|medium|high|thấp|vừa|cao)$/i);
        if (effortMatch) {
          let eff = effortMatch[1].toLowerCase().trim();
          if (eff === "thấp") eff = "low";
          else if (eff === "vừa") eff = "medium";
          else if (eff === "cao") eff = "high";
          try {
            const effResp = await axios.post(`${AGY_ENGINE_URL}/api/set_effort`, { effort: eff }, { timeout: 5000 });
            const effData = effResp.data;
            if (effData.ok) {
              await sendSafeMessage(api, {
                msg: `✅ Dạ Sếp, em đã đổi mức độ suy luận (Effort) sang: ${effData.effort.toUpperCase()}!`,
                quote: msg.data
              }, threadId, ThreadType.User);
              return;
            }
          } catch (e) {}
        }

        // 4. Lệnh tạm dừng phản hồi (Tắt Bé Heo)
        if (/^\/(pause|stop|tat|nghi)\s*$/i.test(userPrompt.trim()) || /^(?:heo\s+)?(?:tạm\s+)?(?:nghỉ|dừng|tắt)\s*(?:đi|nhé|nha)?$/i.test(userPrompt.trim())) {
          try {
            await axios.post(`${AGY_ENGINE_URL}/api/toggle_pause`, { paused: true }, { timeout: 5000 });
            await sendSafeMessage(api, {
              msg: `⏸️ Dạ Sếp, em Heo xin phép tạm dừng phản hồi (chế độ nghỉ ngơi). Khi cần Sếp chỉ cần nhắn "/start" (hoặc "Heo bật lên") hoặc bấm nút BẬT trên Web UI là em kích hoạt lại ngay ạ!`,
              quote: msg.data
            }, threadId, ThreadType.User);
            return;
          } catch (e) {}
        }

        // 5. Lệnh kích hoạt lại (Bật Bé Heo)
        if (/^\/(start|resume|bat|tieptuc)\s*$/i.test(userPrompt.trim()) || /^(?:heo\s+)?(?:bật|hoạt động|dậy)\s*(?:lại|đi|nhé|nha)?$/i.test(userPrompt.trim())) {
          try {
            await axios.post(`${AGY_ENGINE_URL}/api/toggle_pause`, { paused: false }, { timeout: 5000 });
            await sendSafeMessage(api, {
              msg: `▶️ Dạ em Heo đã quay trở lại trực chiến 100%! Em sẵn sàng nhận việc rồi, Sếp giao việc cho em nhé! 🥰✨`,
              quote: msg.data
            }, threadId, ThreadType.User);
            return;
          } catch (e) {}
        }

        // Kiểm tra xem Heo có đang tạm dừng không
        try {
          const stCheck = await axios.get(`${AGY_ENGINE_URL}/api/status`, { timeout: 3000 });
          if (stCheck.data?.bot_paused) {
            log(`[1-1 ${BOSS_NAME}] Heo đang ở chế độ tạm dừng, bỏ qua phản hồi.`);
            return;
          }
        } catch (e) {}

        await api.sendTypingEvent(threadId, ThreadType.User).catch(() => {});
        const typingInterval = setInterval(() => {
          api.sendTypingEvent(threadId, ThreadType.User).catch(() => {});
        }, 4000);

        // Phản hồi xác nhận tức thì: "Heo nghe ạ , chờ heo chút ...."
        try {
          await sendSafeMessage(api, { msg: "Heo nghe ạ , chờ heo chút ....", quote: msg.data }, threadId, ThreadType.User);
          log(`[1-1 ${BOSS_NAME}] Đã gửi xác nhận: "Heo nghe ạ , chờ heo chút ...."`);
        } catch (e) {}

        try {
          const resp = await axios.post(`${AGY_ENGINE_URL}/api/chat`, {
            session_id: `zalo_user_${threadId}`,
            prompt: userPrompt,
            sender_name: "${BOSS_NAME}",
            is_group: false,
            is_boss: true,
            sender_uid: BOSS_UID
          }, { timeout: 300000 });

          const data = resp.data;
          if (data && data.ok) {
            const answer = data.answer || "Dạ em đã hoàn thành.";
            const files = data.files || [];

            let sentRes = null;
            if (files.length > 0) {
              sentRes = await sendSafeMessage(api, {
                msg: answer,
                attachments: files,
                quote: msg.data
              }, threadId, ThreadType.User);
              log(`[1-1 ${BOSS_NAME}] Đã gửi phản hồi kèm ${files.length} file đính kèm!`);
            } else {
              sentRes = await sendSafeMessage(api, {
                msg: answer,
                quote: msg.data
              }, threadId, ThreadType.User);
              log(`[1-1 ${BOSS_NAME}] Đã gửi phản hồi thành công.`);
            }

            const sentMsgId = sentRes?.data?.msgId || sentRes?.msgId || "";
            // Lưu phản hồi của bot vào lịch sử 1-1 với Sếp
            appendGroupHistory("boss_1on1", {
              time: new Date().toISOString(),
              msgId: String(sentMsgId),
              senderUid: String(ownId || "bot"),
              senderName: "Em Heo",
              text: answer
            });
          }
        } catch (apiErr) {
          log(`[1-1 ${BOSS_NAME}] Lỗi AGY Engine: ${apiErr.message}`);
          await sendSafeMessage(api, {
            msg: `Dạ Sếp ơi, hệ thống em bị gián đoạn kết nối chút xíu: ${apiErr.message}. Em đang kiểm tra lại ngay ạ!`,
            quote: msg.data
          }, threadId, ThreadType.User).catch(() => {});
        } finally {
          clearInterval(typingInterval);
        }
        return;
      }

      // 4. CHAT NHÓM (GROUP CHAT)
      if (msgType === ThreadType.Group) {
        // Lấy tên người gửi và tên nhóm thời gian thực
        const senderName = await getUserDisplayName(api, senderUid);
        const groupDetails = await getGroupDetails(api, threadId);

        // Âm thầm lưu lịch sử nhóm vào file để ghi nhớ ngữ cảnh và hỗ trợ Sếp
        appendGroupHistory(threadId, {
          time: new Date().toISOString(),
          msgId: String(msgId || ""),
          senderUid: String(senderUid),
          senderName,
          text: rawContent
        });

        // ĐIỀU KIỆN KÍCH HOẠT TRONG GROUP CHAT:
        // 1. Tag menu Zalo chính thức (@) trỏ vào tài khoản bot
        const mentions = msg.data?.mentions || [];
        const isMentioned = ownId && mentions.some(m => String(m.uid) === String(ownId));
        // 2. Quote tin nhắn của Bot
        const quoteUid = msg.data?.quote?.uidFrom;
        const isQuotingBot = ownId && String(quoteUid) === String(ownId);
        // 3. Có gõ tag đích danh kèm @: @heo, @Heo, @hêu, @Hêu
        const tagRegex = /@(?:heo|hêu)(?!\p{L})/iu;
        const hasExplicitTag = tagRegex.test(rawContent);
        // 4. Gọi Heo ở đầu câu (Heo ơi, Heo à, Heo nè, Heo cho chị hỏi, Heo giúp, Heo tính, v.v.)
        const startCallRegex = /^\s*(?:ê|alo|nè|dạ)?\s*(?:heo|hêu)(?:\s*(?:ơi|à|nè|này|nhe|nhé|cho|giúp|giùm|hộ|làm|tìm|tính|xem|soạn|viết|tra|hỏi|biết|trả lời|báo|tổng hợp|hỗ trợ|chỉ)(?!\p{L})|\s*$)/iu;
        const hasStartCall = startCallRegex.test(rawContent);
        // 5. Gọi Heo ở cuối câu (..., Heo ơi?, ... hả Heo?)
        const endCallRegex = /[,\s]+(?:heo|hêu)(?:\s*(?:ơi|à|nè|nhe|nhé))?[\s.?!]*$/iu;
        const hasEndCall = endCallRegex.test(rawContent);
        // 6. Cụm từ nhờ/gọi Heo trong câu
        const midCallRegex = /(?:nhờ|kêu|bảo|gọi)\s+(?:heo|hêu)(?!\p{L})/iu;
        const actionCallRegex = /(?:heo|hêu)\s+(?:hỗ trợ|giúp|chỉ|trả lời|nghe|thấy)(?!\p{L})/iu;
        const hasMidCall = midCallRegex.test(rawContent) || actionCallRegex.test(rawContent);
        // 7. Lệnh chuyên môn rõ ràng: /task, /sheet, /doc, /calc, /baocao
        const commandRegex = /^\/(ask|task|sheet|doc|calc|baocao)\b/iu;
        const hasCommand = commandRegex.test(rawContent);

        // QUY TẮC BẤT DI BẤT DỊCH: Khi không kêu tới Heo thì Heo im lặng 100%
        if (!isMentioned && !isQuotingBot && !hasExplicitTag && !hasStartCall && !hasEndCall && !hasMidCall && !hasCommand) {
          return; // IM LẶNG TUYỆT ĐỐI 100%, không xen ngang cuộc trò chuyện khác!
        }

        // Kiểm tra xem Heo có đang ở chế độ tạm dừng không
        try {
          const stCheck = await axios.get(`${AGY_ENGINE_URL}/api/status`, { timeout: 3000 });
          if (stCheck.data?.bot_paused) {
            log(`[Group ${groupDetails.name}] Bỏ qua vì Bé Heo đang tạm dừng.`);
            return;
          }
        } catch (e) {}

        let cleanPrompt = rawContent
          .replace(/@(?:heo|hêu)\s*(?:ơi|ạ)?/giu, " ")
          .replace(/^\s*(?:ê|alo|nè|dạ)?\s*(?:heo|hêu)\s*(?:ơi|à|nè|này|nhe|nhé)?\s*/giu, " ")
          .replace(commandRegex, "")
          .trim();

        if (msg.data?.quote && msg.data.quote.msg) {
          cleanPrompt = `[Trích dẫn tin nhắn: "${msg.data.quote.msg}"]\n\nYêu cầu: ${cleanPrompt || "Hãy xử lý nội dung trên"}`.trim();
        }

        const isBoss = Boolean(senderUid && String(senderUid) === BOSS_UID);
        await api.sendTypingEvent(threadId, ThreadType.Group).catch(() => {});
        const typingInterval = setInterval(() => {
          api.sendTypingEvent(threadId, ThreadType.Group).catch(() => {});
        }, 4000);

        // Phản hồi xác nhận tức thì trong nhóm: "Heo nghe ạ , chờ heo chút ...."
        try {
          await sendSafeMessage(api, { msg: "Heo nghe ạ , chờ heo chút ....", quote: msg.data }, threadId, ThreadType.Group);
          log(`[Group ${groupDetails.name}] Đã gửi xác nhận: "Heo nghe ạ , chờ heo chút ...."`);
        } catch (e) {}

        try {
          const resp = await axios.post(`${AGY_ENGINE_URL}/api/chat`, {
            session_id: `zalo_group_${threadId}`,
            prompt: cleanPrompt || rawContent,
            sender_name: senderName,
            sender_uid: String(senderUid),
            group_id: String(threadId),
            group_name: groupDetails.name,
            is_boss: isBoss,
            is_group: true
          }, { timeout: 300000 });

          const data = resp.data;
          if (data && data.ok) {
            const answer = data.answer || "Dạ em đã hoàn thành.";
            const files = data.files || [];

            let sentRes = null;
            if (files.length > 0) {
              sentRes = await sendSafeMessage(api, {
                msg: answer,
                attachments: files,
                quote: msg.data
              }, threadId, ThreadType.Group);
              log(`[Group ${groupDetails.name}] Đã gửi kết quả kèm ${files.length} file vào nhóm!`);
            } else {
              sentRes = await sendSafeMessage(api, {
                msg: answer,
                quote: msg.data
              }, threadId, ThreadType.Group);
              log(`[Group ${groupDetails.name}] Đã gửi phản hồi vào nhóm.`);
            }

            const sentMsgId = sentRes?.data?.msgId || sentRes?.msgId || "";
            // Lưu phản hồi của bot vào lịch sử nhóm
            appendGroupHistory(threadId, {
              time: new Date().toISOString(),
              msgId: String(sentMsgId),
              senderUid: String(ownId || "bot"),
              senderName: "Em Heo",
              text: answer
            });
          }
        } catch (apiErr) {
          log(`[Group ${groupDetails.name}] Lỗi AGY Engine: ${apiErr.message}`);
          // Trong group nếu lỗi nội bộ thì im lặng không spam lỗi kỹ thuật ra nhóm
        } finally {
          clearInterval(typingInterval);
        }
      }
    } catch (err) {
      log(`Lỗi xử lý tin nhắn: ${err.message}`);
    }
  });

  // Lắng nghe Reaction (thả tim, like, haha, wow, buồn, phẫn nộ)
  api.listener.on("reaction", async (reaction) => {
    try {
      const threadId = reaction.threadId;
      const isGroup = reaction.isGroup;
      const senderUid = reaction.data?.uidFrom;
      const rData = reaction.data?.content || {};
      const rIcon = rData.rIcon;
      const rType = rData.rType;
      const rMsgList = rData.rMsg || [];
      const targetGMsgId = (rMsgList.length > 0 && rMsgList[0].gMsgID) ? String(rMsgList[0].gMsgID) : "";

      const reactionInfo = parseReactionDetails(rIcon, rType);
      const senderName = await getUserDisplayName(api, senderUid);
      const targetChannel = isGroup ? threadId : "boss_1on1";
      const targetPreview = findMessageSnippet(targetChannel, targetGMsgId);

      const targetLog = targetPreview ? ` vào "${targetPreview}..."` : '';
      log(`💖 [Reaction ${isGroup ? 'Group' : '1-1'} ${threadId}]: ${senderName} thả ${reactionInfo.icon} (${reactionInfo.name})${targetLog} [${reactionInfo.sentiment}]`);

      const record = {
        time: new Date().toISOString(),
        type: "reaction",
        senderUid: String(senderUid),
        senderName,
        targetMsgId: targetGMsgId,
        targetPreview: targetPreview,
        icon: reactionInfo.icon,
        iconName: reactionInfo.name,
        sentiment: reactionInfo.sentiment,
        meaning: reactionInfo.meaning
      };

      appendGroupHistory(targetChannel, record);
    } catch (rErr) {
      log(`⚠️ Lỗi xử lý reaction: ${rErr.message}`);
    }
  });

  api.listener.on("connected", () => {
    log("🟢 Zalo WebSocket KẾT NỐI TRỰC TIẾP thành công (Live Connected)!");
  });
  api.listener.on("closed", (code, reason) => {
    log(`⚠️ WebSocket đóng (${code}: ${reason}). Tự động khởi động lại...`);
    setTimeout(() => process.exit(1), 1000);
  });
  api.listener.on("disconnected", () => {
    log(`⚠️ WebSocket mất kết nối. Khôi phục sau 1s...`);
    setTimeout(() => process.exit(1), 1000);
  });
  api.listener.on("error", (err) => {
    log(`⚠️ WebSocket lỗi: ${err && err.message ? err.message : err}. Khởi động lại sau 1s...`);
    setTimeout(() => process.exit(1), 1000);
  });

  api.listener.start({ retryOnClose: true });
  log("👂 AGY Zalo Listener đang chạy nền (retryOnClose=true)...");
}

startBridge().catch((err) => {
  log(`Lỗi fatal: ${err.message}`);
});
