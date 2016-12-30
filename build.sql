-- phpMyAdmin SQL Dump
-- version 4.2.12deb2+deb8u1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Aug 03, 2016 at 02:51 AM
-- Server version: 5.5.44-0+deb8u1
-- PHP Version: 5.6.22-0+deb8u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `chromecasts`
--

-- --------------------------------------------------------

--
-- Table structure for table `commands`
--

CREATE TABLE IF NOT EXISTS commands (
  `ID` int(11) NOT NULL PRIMARY KEY,
  `command` varchar(99) COLLATE latin1_general_ci NOT NULL,
  `slot` varchar(99) COLLATE latin1_general_ci NOT NULL,
  `type_of_media` varchar(99) COLLATE latin1_general_ci DEFAULT NULL,
  `TIMESTAMP` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM AUTO_INCREMENT=149 DEFAULT CHARSET=latin1 COLLATE=latin1_general_ci;

--
-- AUTO_INCREMENT for table `commands`
--
ALTER TABLE commands
MODIFY ID int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=149;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
