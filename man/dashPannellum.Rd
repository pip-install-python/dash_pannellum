% Auto-generated: do not edit by hand
\name{dashPannellum}

\alias{dashPannellum}

\title{DashPannellum component}

\description{
DashPannellum is a component for displaying panoramic images and videos. It supports various modes including tours, multi-resolution images, and 360° videos.
}

\usage{
dashPannellum(id=NULL, autoLoad=NULL, currentScene=NULL,
customControls=NULL, height=NULL, multiRes=NULL, pitch=NULL,
showCenterDot=NULL, tour=NULL, video=NULL, width=NULL,
yaw=NULL)
}

\arguments{
\item{id}{Character. The ID used to identify this component in Dash callbacks.}

\item{autoLoad}{Logical. If true, automatically loads the panorama without user interaction.}

\item{currentScene}{Character. The ID of the current scene in tour mode.}

\item{customControls}{Logical. If true, enables custom controls for the panorama viewer.}

\item{height}{Character. The height of the panorama viewer.}

\item{multiRes}{Named list. Configuration object for multi-resolution panoramas.}

\item{pitch}{Numeric. The current pitch of the panorama view.}

\item{showCenterDot}{Logical. If true, displays a center dot in the panorama viewer.}

\item{tour}{Named list. Configuration object for the tour mode.}

\item{video}{Lists containing elements 'sources', 'poster'.
those elements have the following types:
  - sources (required): . sources has the following type: list of lists containing elements 'src', 'type'.
those elements have the following types:
  - src (character; required)
  - type (character; required)s
  - poster (character; optional). Configuration object for video panoramas.}

\item{width}{Character. The width of the panorama viewer.}

\item{yaw}{Numeric. The current yaw of the panorama view.}
}

\value{named list of JSON elements corresponding to React.js properties and their values}

