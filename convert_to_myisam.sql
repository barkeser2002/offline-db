-- ═══════════════════════════════════════════════════════════════════════════
-- MEVCUT TABLOLARI InnoDB'DEN MyISAM'A DÖNÜŞTÜR
-- ═══════════════════════════════════════════════════════════════════════════
-- Kullanım: mysql -u root -p anime_db < convert_to_myisam.sql
-- 
-- NOT: Foreign key'ler MyISAM'da desteklenmez, bu yüzden önce kaldırılır.
-- ═══════════════════════════════════════════════════════════════════════════

-- Foreign key kontrollerini kapat
SET FOREIGN_KEY_CHECKS = 0;

-- video_links tablosu
ALTER TABLE video_links DROP FOREIGN KEY IF EXISTS video_links_ibfk_1;
ALTER TABLE video_links DROP FOREIGN KEY IF EXISTS video_links_ibfk_2;
ALTER TABLE video_links ENGINE = MyISAM;

-- anime_sources tablosu
ALTER TABLE anime_sources DROP FOREIGN KEY IF EXISTS anime_sources_ibfk_1;
ALTER TABLE anime_sources DROP FOREIGN KEY IF EXISTS anime_sources_ibfk_2;
ALTER TABLE anime_sources ENGINE = MyISAM;

-- episodes tablosu
ALTER TABLE episodes DROP FOREIGN KEY IF EXISTS episodes_ibfk_1;
ALTER TABLE episodes ENGINE = MyISAM;

-- anime_producers tablosu
ALTER TABLE anime_producers DROP FOREIGN KEY IF EXISTS anime_producers_ibfk_1;
ALTER TABLE anime_producers DROP FOREIGN KEY IF EXISTS anime_producers_ibfk_2;
ALTER TABLE anime_producers ENGINE = MyISAM;

-- anime_studios tablosu
ALTER TABLE anime_studios DROP FOREIGN KEY IF EXISTS anime_studios_ibfk_1;
ALTER TABLE anime_studios DROP FOREIGN KEY IF EXISTS anime_studios_ibfk_2;
ALTER TABLE anime_studios ENGINE = MyISAM;

-- anime_themes tablosu
ALTER TABLE anime_themes DROP FOREIGN KEY IF EXISTS anime_themes_ibfk_1;
ALTER TABLE anime_themes DROP FOREIGN KEY IF EXISTS anime_themes_ibfk_2;
ALTER TABLE anime_themes ENGINE = MyISAM;

-- anime_genres tablosu
ALTER TABLE anime_genres DROP FOREIGN KEY IF EXISTS anime_genres_ibfk_1;
ALTER TABLE anime_genres DROP FOREIGN KEY IF EXISTS anime_genres_ibfk_2;
ALTER TABLE anime_genres ENGINE = MyISAM;

-- anime_titles tablosu
ALTER TABLE anime_titles DROP FOREIGN KEY IF EXISTS anime_titles_ibfk_1;
ALTER TABLE anime_titles ENGINE = MyISAM;

-- Ana tablolar
ALTER TABLE sources ENGINE = MyISAM;
ALTER TABLE producers ENGINE = MyISAM;
ALTER TABLE studios ENGINE = MyISAM;
ALTER TABLE themes ENGINE = MyISAM;
ALTER TABLE genres ENGINE = MyISAM;
ALTER TABLE animes ENGINE = MyISAM;

-- Foreign key kontrollerini aç
SET FOREIGN_KEY_CHECKS = 1;

-- Sonucu kontrol et
SELECT TABLE_NAME, ENGINE 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
ORDER BY TABLE_NAME;

SELECT '✓ Tüm tablolar MyISAM\'a dönüştürüldü!' AS Sonuc;
