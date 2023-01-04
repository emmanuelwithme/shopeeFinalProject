create table IF NOT EXISTS users ( 
id int not null auto_increment, 
name varchar(20) not null, 
email varchar(20) not null, 
password char(80) not null, 
primary key (id) 
);