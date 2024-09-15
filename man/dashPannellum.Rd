% Auto-generated: do not edit by hand
\name{dashPannellum}

\alias{dashPannellum}

\title{DashPannellum component}

\description{

}

\usage{
dashPannellum(id=NULL, autoLoad=NULL, compass=NULL, currentScene=NULL,
customControls=NULL, height=NULL, multiRes=NULL,
northOffset=NULL, pitch=NULL, showCenterDot=NULL, tour=NULL,
useHttpStreaming=NULL, video=NULL, width=NULL, yaw=NULL)
}

\arguments{
\item{id}{Character. The ID used to identify this component in Dash callbacks.}

\item{autoLoad}{Logical. If true, automatically loads the panorama without user interaction.}

\item{compass}{Logical. If true, displays a compass in the panorama viewer.}

\item{currentScene}{Character. The ID of the current scene in tour mode.}

\item{customControls}{Logical. If true, enables custom controls for the panorama viewer.}

\item{height}{Character. The height of the panorama viewer.}

\item{multiRes}{Named list. Configuration object for multi-resolution panoramas.}

\item{northOffset}{Numeric. The offset, in degrees, of the center of the panorama from North.}

\item{pitch}{Numeric. The current pitch of the panorama view.}

\item{showCenterDot}{Logical. If true, displays a center dot in the panorama viewer.}

\item{tour}{Named list. Configuration object for the tour mode.}

\item{useHttpStreaming}{Logical. If true, enables HTTP streaming support for video.}

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

