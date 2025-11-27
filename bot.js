const { Telegraf, Markup } = require('telegraf');
const express = require('express');
const csv = require('csv-parser');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

// --- НАСТРОЙКИ ---
const BOT_TOKEN = 'ВСТАВЬ_СЮДА_ТОКЕН_БОТА'; 
// Сюда мы вставим ссылку от Ngrok на этапе запуска (см. инструкцию ниже)
let WEB_APP_URL = 'https://google.com'; 

const PORT = 3000;

// --- ЗАГРУЗКА БАЗЫ ---
const universities = [];
fs.createReadStream('database.csv')
  .pipe(csv({ separator: ';' }))
  .on('data', (row) => {
    universities.push({
      name: row.name,
      city: row.city,
      program: row.program,
      subjects: row.subjects ? row.subjects.split(',') : [],
      score: parseInt(row.score) || 0
    });
  })
  .on('end', () => console.log(`📚 База загружена: ${universities.length} вузов`));

// --- СЕРВЕР EXPRESS (САЙТ) ---
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/search', (req, res) => {
  const { subjects, score } = req.body;
  
  const results = universities.filter(uni => {
    // Проходной балл вуза <= твоих баллов
    const scorePass = uni.score <= score;
    // Все предметы вуза есть в твоем списке
    const subjectsPass = uni.subjects.every(subj => subjects.includes(subj));
    return scorePass && subjectsPass;
  });

  res.json(results);
});

app.listen(PORT, () => console.log(`🌍 Сайт работает на порту ${PORT}`));

// --- ТЕЛЕГРАМ БОТ ---
const bot = new Telegraf(BOT_TOKEN);

bot.start((ctx) => {
  ctx.reply(
    'Привет! Нажми кнопку ниже, чтобы найти вуз:',
    Markup.keyboard([
      Markup.button.webApp('🔍 Поиск вузов', WEB_APP_URL)
    ]).resize()
  );
});

bot.launch().then(() => console.log('🤖 Бот запущен!'));

// Обработка остановки
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));