drop database candle_db;
create database candle_db;
use candle_db;
create table tokens
(
	token INT NOT NULL primary key,
    scrip varchar(50)
);
show tables;